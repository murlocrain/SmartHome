/*
 * 设备控制命令定义
 *
 * 命令值编码约定：
 *   0x01-0x0F  基础命令（开关等，无附加参数）
 *   0x0A-0x0F  参数化命令（需配合 env_event_t.param 使用）
 *   0x10-0x1FF 灯光颜色命令（param 编码在 iot_cmd 低 8 位: 0x100+color）
 *   0x20-0x2FF 灯光亮度等级（0x200+level，旧 LIGHT_LEVEL 1-5）
 *   0x30-0x3FF 灯光模式（0x300+mode）
 */
#ifndef __ENV_CONTROL_H__
#define __ENV_CONTROL_H__

/* ── 基础命令 ── */
#define ENV_CMD_LIGHT_ON         0x01
#define ENV_CMD_LIGHT_OFF        0x02
#define ENV_CMD_MOTOR_ON         0x03
#define ENV_CMD_MOTOR_OFF        0x04
#define ENV_CMD_BEEP_PLAY        0x05
#define ENV_CMD_LIGHT_COLOR_NEXT  0x06
#define ENV_CMD_LIGHT_LEVEL_UP    0x07
#define ENV_CMD_LIGHT_LEVEL_DOWN  0x08
#define ENV_CMD_LIGHT_MODE_TOGGLE 0x09

/* ── 参数化命令（需配合 env_event_t.param）── */
#define ENV_CMD_MOTOR_SPEED      0x0A  /* param = speed 0-100 (%) */
#define ENV_CMD_BEEP_TONE        0x0B  /* param = (freq_hz<<16)|(duration_ms&0xFFFF) */
#define ENV_CMD_LIGHT_BRIGHTNESS  0x0C  /* param = brightness 0-255 */
#define ENV_CMD_BEEP_SONG        0x0D  /* param = song_id 0-2 */
#define ENV_CMD_BEEP_STOP        0x0E  /* 立即停止蜂鸣器播放 */

/*
 * env_iot_cmd_process 处理单个命令（旧接口，param 由调用方根据 iot_cmd 解码）。
 * 新增 ENV_CMD_MOTOR_SPEED / BEEP_TONE / LIGHT_BRIGHTNESS 时，
 * 应使用 env_iot_cmd_process_ex(iot_cmd, param)。
 */
void env_iot_cmd_process(int iot_cmd);
void env_iot_cmd_process_ex(int iot_cmd, int param);

#endif
