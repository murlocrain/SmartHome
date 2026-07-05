/*
 * 事件系统：用于华为云命令 → env_control 的异步分发。
 * env_event_t.param 承载附加参数（速度%、时长ms、频率Hz、亮度0-255等）。
 *
 * param 编码约定（根据 env_event_type_t 和 iot_cmd 解码）：
 *   - ENV_CMD_MOTOR_SPEED:      param = speed 0-100
 *   - ENV_CMD_BEEP_TONE:        param = (freq_hz << 16) | (duration_ms & 0xFFFF)
 *   - ENV_CMD_LIGHT_BRIGHTNESS: param = brightness 0-255
 *   - ENV_CMD_LIGHT_COLOR_NEXT..TOGGLE: param 通过 iot_cmd 编码（0x1xx/0x2xx/0x3xx）
 *   - 其他命令:                 param = 0（未使用）
 */
#ifndef __ENV_EVENT_H__
#define __ENV_EVENT_H__

#include <stdint.h>

typedef enum {
    env_event_iot_cmd = 1,
} env_event_type_t;

typedef struct {
    env_event_type_t event;
    int iot_cmd;
    int param;   /* 附加参数 */
} env_event_t;

void env_event_init(void);
void env_event_send(const env_event_t *event);
int env_event_wait(env_event_t *event, int timeout_ms);

#endif
