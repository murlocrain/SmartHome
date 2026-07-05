#ifndef _DRV_LIGHT_H__
#define _DRV_LIGHT_H__

#include <stdbool.h>

#define LIGHT_COLOR_WHITE    0
#define LIGHT_COLOR_RED      1
#define LIGHT_COLOR_GREEN    2
#define LIGHT_COLOR_BLUE     3
#define LIGHT_COLOR_YELLOW   4
#define LIGHT_COLOR_CYAN     5
#define LIGHT_COLOR_PURPLE   6
#define LIGHT_COLOR_MAX      7

#define LIGHT_MODE_STATIC    0
#define LIGHT_MODE_BREATH    1
#define LIGHT_MODE_MAX       2

#define LIGHT_LEVEL_MIN      1
#define LIGHT_LEVEL_MAX      5

/* 0-255 级精细亮度（与 LIGHT_LEVEL 1-5 独立并存） */
#define LIGHT_BRIGHTNESS_MIN  0
#define LIGHT_BRIGHTNESS_MAX  255

void light_dev_init(void);
void light_set_state(bool state);
int get_light_state(void);

void light_set_color(int color);
int get_light_color(void);

/* 1-5 粗粒度亮度，兼容旧接口 */
void light_set_level(int level);
int get_light_level(void);

/* 0-255 精细亮度，0=灭，255=最亮 */
void light_set_brightness(int brightness);
int get_light_brightness(void);

void light_set_mode(int mode);
int get_light_mode(void);

/*
 * 调试用 LED 闪烁：直接驱动 RGB PWM 点亮指定颜色，持续 duration_ms 后熄灭。
 * 不影响当前灯光状态机（light_task 会在下一次循环自动恢复正确状态）。
 * r/g/b 取值 0-255，duration_ms 建议 100-500。
 */
void light_debug_flash(int r, int g, int b, int duration_ms);

#endif
