/*
 * 语音控制模块：SU-03T 语音命令接收与处理。
 *
 * 架构（对齐参考项目 e1 su_03t.c）：
 *   - UART2 在线程内部初始化，BLOCK 模式读取
 *   - 始终使用大端 2 字节裸码解析（SU-03T 配置为 "2字节HEX输出"）
 *   - 匹配命令后通过 env_control 分发
 *   - AA 帧头协议仅用于 RK2206→SU-03T 方向发送反馈（su03t_send_*），
 *     不用于命令接收。SU-03T→RK2206 命令固定为 2 字节大端裸码。
 *
 * LED 反馈（非阻塞优先级：红/橙 > 绿 > 蓝）：
 *   蓝色 = 收到 UART 任意数据（短暂 30ms）
 *   绿色 = 语音命令匹配成功并执行
 *   橙色 = 语音命令匹配但被状态检查拒绝
 *   红色 = 收到数据但命令码无法匹配
 *   黄色 = 帧校验和/长度错误（AA 帧保留）
 */

#include "voice_ctrl.h"
#include "env_monitor.h"
#include "env_control.h"
#include "env_event.h"
#include "env_iot.h"
#include "drv_light.h"

#include <stdio.h>
#include <string.h>

#include "iot_errno.h"
#include "iot_uart.h"
#include "los_task.h"
#include "ohos_init.h"

#define UART2_HANDLE          EUART2_M1
#define VOICE_DEBUG_LEVEL     2

/* ── 协议常量 ── */
#define SU03T_FRAME_HEADER    0xAA

/* ── SU-03T 语音反馈消息号 ── */
#define SU03T_MSG_LIGHT_ALREADY_DIM   0x10  /* "灯光已处于最暗状态，无法继续调暗" */
#define SU03T_MSG_LIGHT_ALREADY_OFF   0x11  /* "灯光当前处于关闭状态，无需执行关灯操作" */

voice_debug_t g_voice_debug;

/* ── 语音命令 → ENV_CMD 映射表 ── */
static const struct {
    uint16_t voice_code;
    int      env_cmd;
    const char *desc;
} g_voice_cmd_map[] = {
    { 0x0001, ENV_CMD_LIGHT_ON,          "开灯" },
    { 0x0002, ENV_CMD_LIGHT_OFF,         "关灯" },
    { 0x0003, ENV_CMD_MOTOR_ON,          "电机开" },
    { 0x0004, ENV_CMD_MOTOR_OFF,         "电机关" },
    { 0x0005, ENV_CMD_BEEP_PLAY,         "蜂鸣器" },
    { 0x0006, ENV_CMD_LIGHT_COLOR_NEXT,  "换颜色" },
    { 0x0007, ENV_CMD_LIGHT_LEVEL_UP,    "调亮" },
    { 0x0008, ENV_CMD_LIGHT_LEVEL_DOWN,  "调暗" },
    { 0x0009, ENV_CMD_LIGHT_MODE_TOGGLE, "切换模式" },
    { 0x000A, ENV_CMD_MOTOR_SPEED,       "电机调速" },
    { 0x000B, ENV_CMD_LIGHT_BRIGHTNESS,  "灯光亮度" },
    { 0x0301, -1,                        "查询温度" },
    { 0x0302, -2,                        "查询湿度" },
    { 0x0303, -3,                        "查询光照" },
};

static void bytes_to_hex(const uint8_t *data, int len, char *out, int out_size)
{
    int pos = 0;
    for (int i = 0; i < len && pos + 3 < out_size; i++)
        pos += snprintf(out + pos, out_size - pos, "%02X ", data[i]);
    if (pos > 0 && out[pos - 1] == ' ') out[pos - 1] = '\0';
}

static void voice_execute_cmd(uint16_t cmd)
{
    for (int i = 0; i < (int)(sizeof(g_voice_cmd_map) / sizeof(g_voice_cmd_map[0])); i++) {
        if (cmd == g_voice_cmd_map[i].voice_code) {
            printf("[voice] MATCHED cmd=0x%04X -> %s\n", cmd, g_voice_cmd_map[i].desc);

            /* ── 状态判断: 调暗灯光 -> 最低亮度时拒绝 ── */
            if (g_voice_cmd_map[i].env_cmd == ENV_CMD_LIGHT_LEVEL_DOWN) {
                if (get_light_level() <= LIGHT_LEVEL_MIN) {
                    printf("[voice] REJECT 0x%04X: light already at min brightness (level=%d)\n",
                           cmd, get_light_level());
                    su03t_send_uchar_msg(SU03T_MSG_LIGHT_ALREADY_DIM, 0);
                    light_debug_flash(255, 165, 0, 300); /* 橙色: 命令识别但被拒绝 */
                    g_voice_debug.last_cmd = cmd;
                    g_voice_debug.last_cmd_matched = 1;
                    g_voice_debug.voice_cmd_count++;
                    return;
                }
            }

            /* ── 状态判断: 关灯 -> 已关闭时拒绝 ── */
            if (g_voice_cmd_map[i].env_cmd == ENV_CMD_LIGHT_OFF) {
                if (!get_light_state()) {
                    printf("[voice] REJECT 0x%04X: light already off\n", cmd);
                    su03t_send_uchar_msg(SU03T_MSG_LIGHT_ALREADY_OFF, 0);
                    light_debug_flash(255, 165, 0, 300); /* 橙色: 命令识别但被拒绝 */
                    g_voice_debug.last_cmd = cmd;
                    g_voice_debug.last_cmd_matched = 1;
                    g_voice_debug.voice_cmd_count++;
                    return;
                }
            }

            light_debug_flash(0, 255, 0, 200);

            /* 传感器查询命令 */
            if (g_voice_cmd_map[i].env_cmd < 0) {
                env_monitor_data_t sensor_data;
                env_sensors_read(&sensor_data);

                switch (g_voice_cmd_map[i].env_cmd) {
                case -1:
                    /* 查询温度 - 用int发送，乘以10保留1位小数，或直接发整数 */
                    su03t_send_int_msg(1, (int32_t)sensor_data.temp_c);
                    printf("[voice] temperature=%.1f C sent\n", sensor_data.temp_c);
                    break;
                case -2:
                    /* 查询湿度 - 用unsigned char发送（0-100） */
                    su03t_send_uchar_msg(2, (uint8_t)sensor_data.humi_pct);
                    printf("[voice] humidity=%.1f %% sent\n", sensor_data.humi_pct);
                    break;
                case -3:
                    /* 查询光照 - 用int发送 */
                    su03t_send_int_msg(3, (int32_t)sensor_data.lux);
                    printf("[voice] illuminance=%.1f lux sent\n", sensor_data.lux);
                    break;
                }
            } else if (g_voice_cmd_map[i].env_cmd == ENV_CMD_MOTOR_SPEED) {
                env_iot_cmd_process_ex(g_voice_cmd_map[i].env_cmd, 50);
            } else if (g_voice_cmd_map[i].env_cmd == ENV_CMD_LIGHT_BRIGHTNESS) {
                env_iot_cmd_process_ex(g_voice_cmd_map[i].env_cmd, 128);
            } else {
                env_iot_cmd_process(g_voice_cmd_map[i].env_cmd);
            }

            env_iot_publish_status();

            g_voice_debug.last_cmd = cmd;
            g_voice_debug.last_cmd_matched = 1;
            g_voice_debug.voice_cmd_count++;
            return;
        }
    }

    /* 未匹配 */
    g_voice_debug.last_cmd = cmd;
    g_voice_debug.last_cmd_matched = 0;
    g_voice_debug.unknown_cmd_count++;
    printf("[voice] UNKNOWN cmd=0x%04X (total unknown:%u)\n",
           cmd, (unsigned)g_voice_debug.unknown_cmd_count);
    light_debug_flash(255, 0, 0, 200);
}

/*
 * AA 帧头协议解析（保留用于参考，当前命令接收路径不使用）
 * 帧格式: AA len cmd_h cmd_l [cs]  （len = 后续字节数，不含 AA 和 cs）
 * 返回: 1=成功(cmd_out有效), 0=数据不足, -1=帧错误
 */
static int parse_aa_frame(const uint8_t *buf, int len, uint16_t *cmd_out)
{
    int pos;

    for (pos = 0; pos < len; pos++) {
        if (buf[pos] == SU03T_FRAME_HEADER)
            break;
    }
    if (pos >= len || pos + 4 > len) return 0;

    uint8_t frame_len = buf[pos + 1];
    if (frame_len < 2 || frame_len > 6) {
        g_voice_debug.frame_len_errors++;
        return -1;
    }

    int total = frame_len + 1;
    int has_cs = (pos + total + 1 <= len) ? 1 : 0;
    if (has_cs) total += 1;
    if (pos + total > len) return 0;

    if (has_cs) {
        uint8_t cs_expect = 0;
        for (int k = pos; k < pos + total - 1; k++)
            cs_expect ^= buf[k];
        if (cs_expect != buf[pos + total - 1]) {
            g_voice_debug.frame_crc_errors++;
#if VOICE_DEBUG_LEVEL >= 1
            printf("[voice] AA CRC error: calc=0x%02X recv=0x%02X\n",
                   cs_expect, buf[pos + total - 1]);
#endif
            light_debug_flash(255, 255, 0, 250);
            return -1;
        }
    }

    uint8_t cmd_h = buf[pos + 2];
    uint8_t cmd_l = buf[pos + 3];
    *cmd_out = (uint16_t)((cmd_h << 8) | cmd_l);

#if VOICE_DEBUG_LEVEL >= 2
    printf("[voice] AA frame len=%d cmd=0x%04X cs=%d OK\n",
           frame_len, *cmd_out, has_cs);
#endif
    return 1;
}

/***************************************************************
* 函数名称: su03t_send_int_msg
* 说    明: 发送int类型数据到语音模块 (AA [msg_id] [4字节int小端])
* 参    数: msg_id 消息号, val 整数值
* 返 回 值: 无
***************************************************************/
void su03t_send_int_msg(uint8_t msg_id, int32_t val)
{
    uint8_t buf[6] = {0};
    uint8_t *p = buf;
    uint8_t *u8_ptr = (uint8_t *)&val;

    *p++ = 0xAA;
    *p++ = msg_id;
    for (int i = 0; i < 4; i++)
        *p++ = u8_ptr[i];

    IoTUartWrite(UART2_HANDLE, buf, p - buf);
    printf("[voice] send int msg=%d val=%d\n", msg_id, (int)val);
}

/***************************************************************
* 函数名称: su03t_send_uchar_msg
* 说    明: 发送unsigned char类型数据到语音模块 (AA [msg_id] [1字节])
* 参    数: msg_id 消息号, val 字节值
* 返 回 值: 无
***************************************************************/
void su03t_send_uchar_msg(uint8_t msg_id, uint8_t val)
{
    uint8_t buf[3] = {0};
    buf[0] = 0xAA;
    buf[1] = msg_id;
    buf[2] = val;

    IoTUartWrite(UART2_HANDLE, buf, sizeof(buf));
    printf("[voice] send uchar msg=%d val=%u\n", msg_id, (unsigned)val);
}

/***************************************************************
* 函数名称: voice_ctrl_thread
* 说    明: 语音模块工作线程（对齐 su_03t_thread 参考模式）
*           在线程内初始化 UART2，BLOCK 模式阻塞读取，收到数据后解析分发。
* 参    数: 无
* 返 回 值: 无
***************************************************************/
static void voice_ctrl_thread(void *arg)
{
    IotUartAttribute attr;
    unsigned int ret;

    (void)arg;

    /* ── UART2 在线程内部初始化（参考模式）── */
    IoTUartDeinit(UART2_HANDLE);

    attr.baudRate = 115200;
    attr.dataBits = IOT_UART_DATA_BIT_8;
    attr.pad = IOT_FLOW_CTRL_NONE;
    attr.parity = IOT_UART_PARITY_NONE;
    attr.rxBlock = IOT_UART_BLOCK_STATE_BLOCK;
    attr.stopBits = IOT_UART_STOP_BIT_1;
    attr.txBlock = IOT_UART_BLOCK_STATE_BLOCK;

    ret = IoTUartInit(UART2_HANDLE, &attr);
    if (ret != IOT_SUCCESS) {
        printf("[voice_ctrl] IoTUartInit failed ret=%d\n", ret);
        g_voice_debug.uart2_init_ok = 0;
        return;
    }

    g_voice_debug.uart2_init_ok = 1;
    g_voice_debug.voice_task_alive = 1;
    g_voice_debug.proto_mode = 1; /* 固定为裸码模式，不做自动检测 */

    printf("\n\n===== [voice_ctrl] UART2 init OK baud=115200 =====\n\n");
    printf("[voice_ctrl] PROTO: fixed raw 2-byte big-endian (aligned with e1 reference)\n");
    printf("[voice_ctrl] LED: green=match orange=rejected red=unknown\n");

    uint32_t loop_count = 0;
    uint8_t rx_buf[2] = {0};
    uint8_t rx_buf_len = 0;

    while (1) {
        uint8_t data[64] = {0};
        uint8_t rec_len = IoTUartRead(UART2_HANDLE, data, sizeof(data));

        loop_count++;

        if ((loop_count % 40) == 0) {
            printf("[voice] heartbeat loop=%u uart_total=%u proto=%d rx_pending=%u\n",
                   (unsigned)loop_count, (unsigned)g_voice_debug.uart_total_bytes,
                   (int)g_voice_debug.proto_mode, (unsigned)rx_buf_len);
        }

        if (rec_len == 0) {
            LOS_Msleep(10);
            continue;
        }

        /* ── 统计 ── */
        g_voice_debug.uart_total_bytes += rec_len;
        g_voice_debug.last_rx_time_ms = LOS_TickCountGet();
        g_voice_debug.last_raw_len = (uint8_t)(rec_len > 8 ? 8 : rec_len);
        memset(g_voice_debug.last_raw, 0, sizeof(g_voice_debug.last_raw));
        memcpy(g_voice_debug.last_raw, data, g_voice_debug.last_raw_len);

        /* ── hex dump ── */
#if VOICE_DEBUG_LEVEL >= 2
        {
            char hex[128] = {0};
            bytes_to_hex(data, rec_len, hex, sizeof(hex));
            printf("[voice] RX %d bytes: [%s]\n", rec_len, hex);
        }
#endif

        /* ── 蓝色LED短暂闪烁: 收到UART数据 ── */
        light_debug_flash(0, 0, 255, 30);

        /* ── 数据喂入 report FIFO（供调试日志使用）── */
        env_sensors_feed_uart_report(data, rec_len);

        /* ── 固定裸码模式：大端 2 字节命令码，支持分块接收 ── */
        for (int i = 0; i < rec_len; i++) {
            rx_buf[rx_buf_len++] = data[i];
            if (rx_buf_len >= 2) {
                uint16_t cmd = (uint16_t)((rx_buf[0] << 8) | rx_buf[1]);
                voice_execute_cmd(cmd);
                rx_buf_len = 0;
            }
        }

        LOS_Msleep(10);
    }
}

void voice_ctrl_init(void)
{
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};

    memset(&g_voice_debug, 0, sizeof(g_voice_debug));

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)voice_ctrl_thread;
    task.uwStackSize = 4096;
    task.pcName = "voice_ctrl";
    task.usTaskPrio = 24;

    if (LOS_TaskCreate(&thread_id, &task) != LOS_OK) {
        printf("[voice_ctrl] task create failed\n");
    } else {
        printf("[voice_ctrl] task created, prio=24\n");
    }
}
