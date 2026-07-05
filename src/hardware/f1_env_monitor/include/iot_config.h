/*
 * 华为云 IoTDA 连接信息
 * ============================================================
 * IOT_DEVICE_ID  = 设备ID（MQTT username、Topic 里的 {device_id}）
 * 产品ID前缀 6a2179727f2e6c302f77aaf8，设备标识码 env_monitor_01
 *
 * ── 命令定义（需在控制台产品模型中添加）──
 *
 * | command_name    | 参数 paras                    | 设备动作                          |
 * |-----------------|-------------------------------|-----------------------------------|
 * | light_control   | onoff: ON/OFF                 | 灯光开/关                         |
 * |                 | brightness: 0-255 (可选)      | 灯光亮度（0=灭,255=最亮）         |
 * |                 | color: 0-6 或颜色名(可选)     | 灯光颜色                          |
 * |                 | level: 1-5 (可选)             | 灯光等级（旧接口,已废弃）         |
 * |                 | mode: 0/1 或 STATIC/BREATH    | 灯光模式                          |
 * | motor_control   | onoff: ON/OFF                 | 电机开/关                         |
 * |                 | speed: 0-100 (可选)           | 电机速度百分比（0=停止）          |
 * | beep_play       | （无参数）→ 播放固定曲谱      | 蜂鸣器播放                        |
 * |                 | duration: N (ms,可选)         | 指定时长，默认频率 800Hz          |
 * |                 | frequency: N (Hz,可选)        | 指定频率，默认时长 2000ms         |
 * |                 | duration + frequency 同时用    | 同时指定频率和时长                |
 * | beep_song       | id: 0/1/2                     | 切换蜂鸣器曲目                    |
 * |                 | 0=小蜜蜂 1=超级玛丽 2=哭砂     | 选择后下次 beep_play 生效         |
 *
 * ── 上报属性 ──
 *   传感器: mq2_adc, sht30_temp_raw, sht30_humi_raw, bh1750_raw,
 *           accel_x/y/z, gyro_x/y/z, mpu_temp_raw, pir_gpio,
 *           key_adc, uart_rx_len, uart_rx_hex, wifi_conn_state,
 *           wifi_rssi, wifi_ip, wifi_band, wifi_frequency
 *   执行器: light_status(ON/OFF), motor_status(ON/OFF)
 */

#ifndef __IOT_CONFIG_H__
#define __IOT_CONFIG_H__

#define IOT_HOST            "274d24a6ed.st1.iotda-device.cn-north-4.myhuaweicloud.com"
#define IOT_DEVICE_ID       "6a2179727f2e6c302f77aaf8_env_monitor_01"
#define IOT_CLIENT_ID       "6a2179727f2e6c302f77aaf8_env_monitor_01_0_0_2026061507"
/* 使用连接信息里的 password（长密钥），不是注册页短 secret */
#define IOT_PASSWORD        "b1c57ea76654ddbff55de16d6b72affc1433b685416c9e2981cc288491e808e4"

#define IOT_SERVICE_ID      "rk2206远程控制"

/* 明文 MQTT 协议，端口 1883 */
#define IOT_PORT            1883

/* 属性上报周期（毫秒） */
#define IOT_REPORT_INTERVAL_MS  10000

#endif
