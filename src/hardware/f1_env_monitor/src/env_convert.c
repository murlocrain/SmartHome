#include "env_convert.h"

#include <stddef.h>

#define ADC_REF_V           3.3f
#define ADC_MAX_COUNT       1024.0f
#define MPU6050_ACCEL_LSB_G 2048.0f   /* ACCEL_CONFIG=0x1C, ±16g */
#define MPU6050_GYRO_LSB_DPS 131.0f   /* 默认 ±250°/s */

void env_monitor_apply_units(env_monitor_data_t *data)
{
    uint16_t temp_raw;
    uint16_t humi_raw;
    int i;

    if (data == NULL) {
        return;
    }

    temp_raw = (uint16_t)(data->sht30_temp_raw & ~0x0003U);
    humi_raw = (uint16_t)(data->sht30_humi_raw & ~0x0003U);

    data->temp_c = 175.0f * (float)temp_raw / 65535.0f - 45.0f;
    data->humi_pct = 100.0f * (float)humi_raw / 65535.0f;
    data->lux = (float)data->bh1750_raw / 1.2f;
    data->mpu_temp_c = (float)data->mpu_temp_raw / 340.0f + 36.53f;
    data->mq2_voltage_v = (float)data->mq2_adc * ADC_REF_V / ADC_MAX_COUNT;
    data->key_voltage_v = (float)data->key_adc * ADC_REF_V / ADC_MAX_COUNT;

    for (i = 0; i < 3; i++) {
        data->accel_g[i] = (float)data->accel[i] / MPU6050_ACCEL_LSB_G;
        data->gyro_dps[i] = (float)data->gyro[i] / MPU6050_GYRO_LSB_DPS;
    }
}
