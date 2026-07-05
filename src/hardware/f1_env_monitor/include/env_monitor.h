#ifndef __ENV_MONITOR_H__
#define __ENV_MONITOR_H__

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    /* 寄存器/ADC 原始读数 */
    unsigned int mq2_adc;
    uint16_t sht30_temp_raw;
    uint16_t sht30_humi_raw;
    uint16_t bh1750_raw;
    short accel[3];
    short gyro[3];
    short mpu_temp_raw;
    int pir_gpio;
    unsigned int key_adc;
    uint8_t uart_rx_len;
    uint8_t uart_rx[16];
    int wifi_conn_state;
    int wifi_rssi;
    unsigned int wifi_ip;
    int wifi_band;
    int wifi_frequency;

    /* env_monitor_apply_units() 填充的物理量 */
    float temp_c;
    float humi_pct;
    float lux;
    float accel_g[3];
    float gyro_dps[3];
    float mpu_temp_c;
    float mq2_voltage_v;
    float key_voltage_v;
} env_monitor_data_t;

void env_sensors_init(void);
void env_sensors_read(env_monitor_data_t *data);
void env_sensors_feed_uart_report(const uint8_t *buf, int len);

void env_monitor_lcd_init(void);
void env_monitor_lcd_load_ui(void);
void env_monitor_lcd_update(const env_monitor_data_t *data);
void env_monitor_lcd_update_voice_debug(void);

void wifi_monitor_start(void);
bool wifi_monitor_is_connected(void);
void wifi_monitor_get_link(env_monitor_data_t *data);

#endif
