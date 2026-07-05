#include "adc_key.h"
#include "drv_beep.h"
#include "drv_light.h"
#include "drv_motor.h"

#include <stdio.h>

#include "iot_adc.h"
#include "iot_errno.h"
#include "los_task.h"

#define KEY_ADC_CHANNEL 7

#define KEY_RELEASED 0
#define KEY_PRESSED  1

static float adc_get_voltage(void)
{
    unsigned int data = 0;

    if (IoTAdcGetVal(KEY_ADC_CHANNEL, &data) != IOT_SUCCESS) {
        return 3.3f;
    }
    return (float)data * 3.3f / 1024.0f;
}

static uint8_t adc_voltage_to_key(float voltage)
{
    if (voltage > 3.2f) {
        return KEY_RELEASE;
    }
    if (voltage > 1.50f) {
        return KEY_K5;
    }
    if (voltage > 1.0f) {
        return KEY_K4;
    }
    if (voltage > 0.5f) {
        return KEY_K6;
    }
    return KEY_K3;
}

static void adc_key_handle(uint8_t key)
{
    int new_val;
    switch (key) {
        case KEY_K3: {
            /* 循环切换：关 → 开灯(白) → 红 → 绿 → 蓝 → 关 */
            if (!get_light_state()) {
                light_set_color(LIGHT_COLOR_WHITE);
                light_set_state(true);
                printf("[key] K3 -> 开灯(白)\n");
            } else {
                switch (get_light_color()) {
                case LIGHT_COLOR_WHITE:
                    light_set_color(LIGHT_COLOR_RED);
                    printf("[key] K3 -> 变红\n");
                    break;
                case LIGHT_COLOR_RED:
                    light_set_color(LIGHT_COLOR_GREEN);
                    printf("[key] K3 -> 变绿\n");
                    break;
                case LIGHT_COLOR_GREEN:
                    light_set_color(LIGHT_COLOR_BLUE);
                    printf("[key] K3 -> 变蓝\n");
                    break;
                case LIGHT_COLOR_BLUE:
                default:
                    light_set_state(false);
                    printf("[key] K3 -> 关灯\n");
                    break;
                }
            }
            break;
        }
        case KEY_K4:
            new_val = (get_light_level() < LIGHT_LEVEL_MAX) ? (get_light_level() + 1) : LIGHT_LEVEL_MIN;
            light_set_level(new_val);
            printf("[key] K4 -> Light level=%d\n", new_val);
            break;
        case KEY_K5:
            motor_set_state(!get_motor_state());
            printf("[key] K5 -> Motor %s\n", get_motor_state() ? "ON" : "OFF");
            break;
        case KEY_K6:
            new_val = (get_light_color() + 1) % LIGHT_COLOR_MAX;
            light_set_color(new_val);
            beep_request_play();
            printf("[key] K6 -> Light color=%d, beep play\n", new_val);
            break;
        default:
            break;
    }
}

static void adc_key_task(void *arg)
{
    int pressed = KEY_RELEASED;
    uint8_t key;

    (void)arg;

    while (1) {
        float voltage = adc_get_voltage();
        key = adc_voltage_to_key(voltage);

        if (key == KEY_RELEASE) {
            pressed = KEY_RELEASED;
        } else if (pressed == KEY_RELEASED) {
            pressed = KEY_PRESSED;
            adc_key_handle(key);
        }

        LOS_Msleep(100);
    }
}

void adc_key_start(void)
{
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};
    unsigned int ret;

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)adc_key_task;
    task.uwStackSize = 2048;
    task.pcName = "adc_key";
    task.usTaskPrio = 23;
    ret = LOS_TaskCreate(&thread_id, &task);
    if (ret != LOS_OK) {
        printf("[adc_key] task create failed: 0x%x\n", ret);
    }
}
