#include "env_monitor.h"
#include "env_control.h"
#include "env_event.h"
#include "env_iot.h"
#include "iot_config.h"
#include "adc_key.h"
#include "drv_beep.h"
#include "drv_light.h"
#include "drv_motor.h"
#include "voice_ctrl.h"

#include <stdio.h>

#include "los_task.h"
#include "ohos_init.h"

#define SAMPLE_INTERVAL_MS 500

static void env_monitor_process(void)
{
    env_monitor_data_t data = {0};
    unsigned int report_ticks = 0;
    unsigned int report_every = IOT_REPORT_INTERVAL_MS / SAMPLE_INTERVAL_MS;

    env_event_init();
    env_monitor_lcd_init();
    env_monitor_lcd_load_ui();
    env_sensors_init();
    light_dev_init();
    motor_dev_init();
    beep_dev_init();
    adc_key_start();
    wifi_monitor_start();
    env_iot_start();
    voice_ctrl_init();

    while (1) {
        env_event_t event = {0};
        if (env_event_wait(&event, 0) == LOS_OK && event.event == env_event_iot_cmd) {
            env_iot_cmd_process_ex(event.iot_cmd, event.param);
            /* 命令执行后立即上报设备状态变化到华为云 */
            env_iot_publish_status();
        }

        env_sensors_read(&data);
        env_monitor_lcd_update(&data);
        env_monitor_lcd_update_voice_debug();

        if (env_iot_is_connected()) {
            report_ticks++;
            if (report_ticks >= report_every) {
                report_ticks = 0;
                env_iot_publish(&data);
            }
        } else {
            report_ticks = 0;
        }

        printf("[env] T:%.1fC H:%.0f%% Lux:%.0f MQ2:%.2fV "
               "Acc:%.2f,%.2f,%.2f g Gyro:%.0f,%.0f,%.0f dps MPU:%.1fC "
               "PIR:%d Key:%.2fV uart:%u wifi:%d rssi:%ddBm cloud:%u\n",
               data.temp_c, data.humi_pct, data.lux, data.mq2_voltage_v,
               data.accel_g[0], data.accel_g[1], data.accel_g[2],
               data.gyro_dps[0], data.gyro_dps[1], data.gyro_dps[2], data.mpu_temp_c,
               data.pir_gpio, data.key_voltage_v, data.uart_rx_len,
               data.wifi_conn_state, data.wifi_rssi, env_iot_is_connected());

        LOS_Msleep(SAMPLE_INTERVAL_MS);
    }
}

void env_monitor_example(void)
{
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};
    unsigned int ret;

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)env_monitor_process;
    task.uwStackSize = 81920;
    task.pcName = "env_monitor";
    task.usTaskPrio = 24;
    ret = LOS_TaskCreate(&thread_id, &task);
    if (ret != LOS_OK) {
        printf("[env_monitor] task create failed: 0x%x\n", ret);
    }
}

APP_FEATURE_INIT(env_monitor_example);
