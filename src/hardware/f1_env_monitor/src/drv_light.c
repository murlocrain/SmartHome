#include "drv_light.h"

#include <stdio.h>

#include "iot_errno.h"
#include "iot_pwm.h"
#include "los_task.h"

#define LED_R_PWM_PORT   EPWMDEV_PWM1_M1
#define LED_G_PWM_PORT   EPWMDEV_PWM0_M1
#define LED_B_PWM_PORT   EPWMDEV_PWM7_M1

#define PWM_FREQ_HZ      1000
#define DUTY_MIN         1
#define DUTY_MAX         99

#define RGB(r, g, b)     (((r) << 16) | ((g) << 8) | (b))
#define GET_R(x)         (((x) >> 16) & 0xFF)
#define GET_G(x)         (((x) >> 8) & 0xFF)
#define GET_B(x)         ((x) & 0xFF)

static const uint32_t g_color_table[LIGHT_COLOR_MAX] = {
    RGB(255, 255, 255),
    RGB(255, 0,   0),
    RGB(0,   255, 0),
    RGB(0,   0,   255),
    RGB(255, 255, 0),
    RGB(0,   255, 255),
    RGB(255, 0,   255),
};

static const char *g_color_name[LIGHT_COLOR_MAX] = {
    "WHITE", "RED", "GREEN", "BLUE", "YELLOW", "CYAN", "PURPLE",
};

static const char *g_mode_name[LIGHT_MODE_MAX] = {
    "STATIC", "BREATH",
};

static volatile bool g_light_on = false;
static volatile int g_light_color = LIGHT_COLOR_WHITE;
static volatile int g_light_level = LIGHT_LEVEL_MAX;
static volatile int g_light_brightness = LIGHT_BRIGHTNESS_MAX;
static volatile int g_light_mode = LIGHT_MODE_STATIC;

static int duty_fix(int duty)
{
    if (duty > DUTY_MAX) duty = DUTY_MAX;
    if (duty < DUTY_MIN) duty = DUTY_MIN;
    return duty;
}

static void pwm_output(int r_duty, int g_duty, int b_duty)
{
    r_duty = duty_fix(r_duty);
    g_duty = duty_fix(g_duty);
    b_duty = duty_fix(b_duty);
    IoTPwmStart(LED_R_PWM_PORT, (unsigned int)r_duty, PWM_FREQ_HZ);
    IoTPwmStart(LED_G_PWM_PORT, (unsigned int)g_duty, PWM_FREQ_HZ);
    IoTPwmStart(LED_B_PWM_PORT, (unsigned int)b_duty, PWM_FREQ_HZ);
}

static void pwm_stop_all(void)
{
    IoTPwmStop(LED_R_PWM_PORT);
    IoTPwmStop(LED_G_PWM_PORT);
    IoTPwmStop(LED_B_PWM_PORT);
}

static void apply_static_light(void)
{
    uint32_t rgb = g_color_table[g_light_color];
    int r = GET_R(rgb);
    int g = GET_G(rgb);
    int b = GET_B(rgb);
    float scale = (float)g_light_brightness / (float)LIGHT_BRIGHTNESS_MAX;
    int r_duty = (int)(((float)r * scale * (float)DUTY_MAX) / 255.0f + 0.5f);
    int g_duty = (int)(((float)g * scale * (float)DUTY_MAX) / 255.0f + 0.5f);
    int b_duty = (int)(((float)b * scale * (float)DUTY_MAX) / 255.0f + 0.5f);
    pwm_output(r_duty, g_duty, b_duty);
}

static void light_task(void *arg)
{
    (void)arg;
    int breath_duty = DUTY_MIN;
    int breath_toggle = 0;
    int breath_color = 0;
    int color_switch_counter = 0;

    while (1) {
        if (!g_light_on) {
            pwm_stop_all();
            LOS_Msleep(100);
            continue;
        }

        if (g_light_mode == LIGHT_MODE_STATIC) {
            apply_static_light();
            LOS_Msleep(100);
        } else {
            uint32_t rgb = g_color_table[breath_color];
            int r = GET_R(rgb);
            int g = GET_G(rgb);
            int b = GET_B(rgb);
            float scale = (float)breath_duty / (float)DUTY_MAX;
            int r_duty = (int)(((float)r * scale * (float)DUTY_MAX) / 255.0f + 0.5f);
            int g_duty = (int)(((float)g * scale * (float)DUTY_MAX) / 255.0f + 0.5f);
            int b_duty = (int)(((float)b * scale * (float)DUTY_MAX) / 255.0f + 0.5f);
            pwm_output(r_duty, g_duty, b_duty);

            if (breath_toggle) {
                breath_duty--;
            } else {
                breath_duty++;
            }
            if (breath_duty >= DUTY_MAX) {
                breath_duty = DUTY_MAX;
                breath_toggle = 1;
            } else if (breath_duty <= DUTY_MIN) {
                breath_duty = DUTY_MIN;
                breath_toggle = 0;
                color_switch_counter++;
                if (color_switch_counter >= 2) {
                    color_switch_counter = 0;
                    breath_color = (breath_color + 1) % LIGHT_COLOR_MAX;
                }
            }
            LOS_Msleep(20);
        }
    }
}

void light_dev_init(void)
{
    unsigned int ret;
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};

    ret = IoTPwmInit(LED_R_PWM_PORT);
    if (ret != IOT_SUCCESS) {
        printf("[light] IoTPwmInit R failed: %u\n", ret);
    }
    ret = IoTPwmInit(LED_G_PWM_PORT);
    if (ret != IOT_SUCCESS) {
        printf("[light] IoTPwmInit G failed: %u\n", ret);
    }
    ret = IoTPwmInit(LED_B_PWM_PORT);
    if (ret != IOT_SUCCESS) {
        printf("[light] IoTPwmInit B failed: %u\n", ret);
    }

    pwm_stop_all();
    g_light_on = false;
    g_light_color = LIGHT_COLOR_WHITE;
    g_light_level = LIGHT_LEVEL_MAX;
    g_light_mode = LIGHT_MODE_STATIC;

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)light_task;
    task.uwStackSize = 2048;
    task.pcName = "light_ctrl";
    task.usTaskPrio = 22;
    ret = LOS_TaskCreate(&thread_id, &task);
    if (ret != LOS_OK) {
        printf("[light] task create failed: 0x%x\n", ret);
    }
}

void light_set_state(bool state)
{
    if (g_light_on == state) {
        return;
    }
    g_light_on = state;
    if (!state) {
        pwm_stop_all();
    }
    printf("[light] state=%s\n", state ? "ON" : "OFF");
}

int get_light_state(void)
{
    return (int)g_light_on;
}

void light_set_color(int color)
{
    if (color < 0 || color >= LIGHT_COLOR_MAX) {
        return;
    }
    g_light_color = color;
    printf("[light] color=%s\n", g_color_name[color]);
}

int get_light_color(void)
{
    return g_light_color;
}

void light_set_level(int level)
{
    /* 1-5 映射到 0-255: 1→51, 2→102, 3→153, 4→204, 5→255 */
    if (level < LIGHT_LEVEL_MIN || level > LIGHT_LEVEL_MAX) {
        return;
    }
    g_light_level = level;
    light_set_brightness(level * (LIGHT_BRIGHTNESS_MAX / LIGHT_LEVEL_MAX));
    printf("[light] level=%d\n", level);
}

int get_light_level(void)
{
    return g_light_level;
}

void light_set_brightness(int brightness)
{
    if (brightness < LIGHT_BRIGHTNESS_MIN) {
        brightness = LIGHT_BRIGHTNESS_MIN;
    }
    if (brightness > LIGHT_BRIGHTNESS_MAX) {
        brightness = LIGHT_BRIGHTNESS_MAX;
    }
    if (brightness == g_light_brightness) {
        return;
    }

    g_light_brightness = brightness;

    if (brightness == 0) {
        /* 亮度为 0 → 关闭 */
        light_set_state(false);
    } else if (!g_light_on) {
        /* 有亮度但灯没开 → 自动打开 */
        light_set_state(true);
    }

    printf("[light] brightness=%d/255\n", brightness);
}

int get_light_brightness(void)
{
    return g_light_brightness;
}

void light_set_mode(int mode)
{
    if (mode < 0 || mode >= LIGHT_MODE_MAX) {
        return;
    }
    g_light_mode = mode;
    printf("[light] mode=%s\n", g_mode_name[mode]);
}

int get_light_mode(void)
{
    return g_light_mode;
}

void light_debug_flash(int r, int g, int b, int duration_ms)
{
    int r_duty = (int)(((float)r * (float)DUTY_MAX) / 255.0f + 0.5f);
    int g_duty = (int)(((float)g * (float)DUTY_MAX) / 255.0f + 0.5f);
    int b_duty = (int)(((float)b * (float)DUTY_MAX) / 255.0f + 0.5f);

    r_duty = (r_duty < DUTY_MIN) ? DUTY_MIN : (r_duty > DUTY_MAX ? DUTY_MAX : r_duty);
    g_duty = (g_duty < DUTY_MIN) ? DUTY_MIN : (g_duty > DUTY_MAX ? DUTY_MAX : g_duty);
    b_duty = (b_duty < DUTY_MIN) ? DUTY_MIN : (b_duty > DUTY_MAX ? DUTY_MAX : b_duty);

    IoTPwmStart(LED_R_PWM_PORT, (unsigned int)r_duty, PWM_FREQ_HZ);
    IoTPwmStart(LED_G_PWM_PORT, (unsigned int)g_duty, PWM_FREQ_HZ);
    IoTPwmStart(LED_B_PWM_PORT, (unsigned int)b_duty, PWM_FREQ_HZ);

    LOS_Msleep(duration_ms);
}
