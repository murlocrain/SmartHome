/*
 * 语音控制模块：SU-03T 语音命令接收与处理
 *
 * 架构（对齐参考项目 su_03t.c）：
 *   - UART2 在线程内部初始化
 *   - 直接读取，大端 2 字节命令码
 *   - 支持裸码模式和 AA 帧头自动检测
 *   - 数据完整性保障：帧头/长度/异或校验
 */

#ifndef __VOICE_CTRL_H__
#define __VOICE_CTRL_H__

#include <stdint.h>

typedef struct {
    /* ── UART 硬件层 ── */
    uint32_t uart_total_bytes;
    uint8_t  uart2_init_ok;

    /* ── 协议检测 ── */
    uint8_t  proto_mode;         /* 0=未检测, 1=裸码, 2=AA帧头 */

    /* ── FIFO 数据层 ── */
    uint8_t  last_raw_len;
    uint8_t  last_raw[8];

    /* ── 时间信息 ── */
    uint32_t last_rx_time_ms;

    /* ── 命令匹配层 ── */
    uint32_t voice_cmd_count;
    uint32_t unknown_cmd_count;
    uint16_t last_cmd;
    uint8_t  last_cmd_matched;

    /* ── 数据完整性 ── */
    uint32_t frame_crc_errors;
    uint32_t frame_len_errors;

    /* ── 任务健康 ── */
    uint8_t  voice_task_alive;
} voice_debug_t;

extern voice_debug_t g_voice_debug;

void voice_ctrl_init(void);
void su03t_send_int_msg(uint8_t msg_id, int32_t val);
void su03t_send_uchar_msg(uint8_t msg_id, uint8_t val);

#endif
