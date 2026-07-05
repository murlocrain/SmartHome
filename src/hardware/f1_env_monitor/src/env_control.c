/*
 * 设备控制逻辑：将 iot_cmd + param 分发到底层驱动。
 */
#include "env_control.h"

#include <stdio.h>

#include "drv_beep.h"
#include "drv_light.h"
#include "drv_motor.h"

void env_iot_cmd_process_ex(int iot_cmd, int param)
{
    int val;
    int freq_hz;
    int duration_ms;

    /* ── 灯光颜色 (0x100-0x1FF) ── */
    if (iot_cmd >= 0x100 && iot_cmd < 0x200) {
        val = iot_cmd - 0x100;
        if (val >= 0 && val < LIGHT_COLOR_MAX) {
            if (!get_light_state()) light_set_state(true);
            light_set_color(val);
        }
        return;
    }

    /* ── 灯光亮度等级 1-5 (0x200-0x2FF，兼容旧接口) ── */
    if (iot_cmd >= 0x200 && iot_cmd < 0x300) {
        val = iot_cmd - 0x200;
        if (val >= LIGHT_LEVEL_MIN && val <= LIGHT_LEVEL_MAX) {
            if (!get_light_state()) light_set_state(true);
            light_set_level(val);
        }
        return;
    }

    /* ── 灯光模式 (0x300-0x3FF) ── */
    if (iot_cmd >= 0x300 && iot_cmd < 0x400) {
        val = iot_cmd - 0x300;
        if (val >= 0 && val < LIGHT_MODE_MAX) {
            if (!get_light_state()) light_set_state(true);
            light_set_mode(val);
        }
        return;
    }

    /* ── 基础 + 参数化命令 ── */
    switch (iot_cmd) {
        case ENV_CMD_LIGHT_ON:
            light_set_state(true);
            printf("[iot_cmd] Light ON\n");
            break;
        case ENV_CMD_LIGHT_OFF:
            light_set_state(false);
            printf("[iot_cmd] Light OFF\n");
            break;
        case ENV_CMD_MOTOR_ON:
            motor_set_state(true);
            printf("[iot_cmd] Motor ON\n");
            break;
        case ENV_CMD_MOTOR_OFF:
            motor_set_state(false);
            printf("[iot_cmd] Motor OFF\n");
            break;
        case ENV_CMD_BEEP_PLAY:
            beep_request_play();
            printf("[iot_cmd] Beep play (melody)\n");
            break;
        case ENV_CMD_LIGHT_COLOR_NEXT:
            light_set_color((get_light_color() + 1) % LIGHT_COLOR_MAX);
            break;
        case ENV_CMD_LIGHT_LEVEL_UP:
            light_set_level(get_light_level() < LIGHT_LEVEL_MAX ? get_light_level() + 1 : LIGHT_LEVEL_MIN);
            break;
        case ENV_CMD_LIGHT_LEVEL_DOWN:
            light_set_level(get_light_level() > LIGHT_LEVEL_MIN ? get_light_level() - 1 : LIGHT_LEVEL_MAX);
            break;
        case ENV_CMD_LIGHT_MODE_TOGGLE:
            light_set_mode(get_light_mode() == LIGHT_MODE_STATIC ? LIGHT_MODE_BREATH : LIGHT_MODE_STATIC);
            break;

        /* ── 参数化命令 ── */
        case ENV_CMD_MOTOR_SPEED:
            motor_set_speed(param);
            printf("[iot_cmd] Motor speed=%d%%\n", param);
            break;
        case ENV_CMD_BEEP_TONE:
            /* param 编码: (freq_hz << 16) | (duration_ms & 0xFFFF) */
            freq_hz = (param >> 16) & 0xFFFF;
            duration_ms = param & 0xFFFF;
            beep_play_tone(freq_hz, duration_ms);
            printf("[iot_cmd] Beep tone freq=%dHz dur=%dms\n", freq_hz, duration_ms);
            break;
        case ENV_CMD_LIGHT_BRIGHTNESS:
            light_set_brightness(param);
            printf("[iot_cmd] Light brightness=%d/255\n", param);
            break;
        case ENV_CMD_BEEP_SONG:
            beep_set_song(param);
            printf("[iot_cmd] Beep song=%d\n", param);
            break;
        case ENV_CMD_BEEP_STOP:
            beep_stop_play();
            printf("[iot_cmd] Beep STOP\n");
            break;

        default:
            printf("[iot_cmd] unknown cmd: 0x%x\n", iot_cmd);
            break;
    }
}

void env_iot_cmd_process(int iot_cmd)
{
    env_iot_cmd_process_ex(iot_cmd, 0);
}
