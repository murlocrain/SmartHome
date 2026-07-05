/*
 * 直流电机驱动：PWM 无级调速 0-100%
 * 硬件端口: EPWMDEV_PWM6_M0, PWM 频率 1kHz
 */
#include "drv_motor.h"

#include <stdio.h>

#include "iot_pwm.h"

#define MOTOR_PWM_HANDLE  EPWMDEV_PWM6_M0
#define MOTOR_PWM_FREQ_HZ 1000
#define MOTOR_DUTY_MAX    99
#define MOTOR_DUTY_MIN    1

static bool g_motor_state = false;
static int  g_motor_speed = 50;   /* 默认 50% */

void motor_dev_init(void)
{
    IoTPwmInit(MOTOR_PWM_HANDLE);
    printf("[motor] init OK, port=EPWM6_M0\n");
}

/* percent → duty 线性映射: 1%→1, 100%→99 */
static unsigned int motor_percent_to_duty(int percent)
{
    int duty;

    if (percent <= 0) {
        return 0;
    }
    if (percent > 100) {
        percent = 100;
    }

    duty = (int)((float)percent * (float)MOTOR_DUTY_MAX / 100.0f + 0.5f);
    if (duty < MOTOR_DUTY_MIN) {
        duty = MOTOR_DUTY_MIN;
    }
    if (duty > MOTOR_DUTY_MAX) {
        duty = MOTOR_DUTY_MAX;
    }
    return (unsigned int)duty;
}

void motor_set_speed(int percent)
{
    if (percent < 0) {
        percent = 0;
    }
    if (percent > 100) {
        percent = 100;
    }

    if (percent == g_motor_speed && g_motor_state) {
        return;
    }

    g_motor_speed = percent;

    if (percent == 0) {
        /* 速度为 0 → 停止 */
        IoTPwmStop(MOTOR_PWM_HANDLE);
        g_motor_state = false;
        printf("[motor] speed=0%% → STOP\n");
    } else {
        unsigned int duty = motor_percent_to_duty(percent);
        IoTPwmStart(MOTOR_PWM_HANDLE, duty, MOTOR_PWM_FREQ_HZ);
        g_motor_state = true;
        printf("[motor] speed=%d%% (duty=%u/99)\n", percent, duty);
    }
}

int get_motor_speed(void)
{
    return g_motor_state ? g_motor_speed : 0;
}

void motor_set_state(bool state)
{
    if (state == g_motor_state && state) {
        return;
    }

    if (state) {
        /* 启动：使用当前保存的速度值 */
        if (g_motor_speed <= 0) {
            g_motor_speed = 50; /* 默认 50% */
        }
        unsigned int duty = motor_percent_to_duty(g_motor_speed);
        IoTPwmStart(MOTOR_PWM_HANDLE, duty, MOTOR_PWM_FREQ_HZ);
        g_motor_state = true;
        printf("[motor] ON speed=%d%% (duty=%u)\n", g_motor_speed, duty);
    } else {
        IoTPwmStop(MOTOR_PWM_HANDLE);
        g_motor_state = false;
        printf("[motor] OFF\n");
    }
}

int get_motor_state(void)
{
    return (int)g_motor_state;
}
