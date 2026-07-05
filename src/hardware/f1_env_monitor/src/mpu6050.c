#include "mpu6050.h"

#include <stddef.h>

#include "iot_i2c.h"
#include "iot_errno.h"
#include "los_task.h"

#define MPU6050_I2C_PORT EI2C0_M2

static void mpu6050_write_reg(uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg, val};
    IoTI2cWrite(MPU6050_I2C_PORT, MPU6050_SLAVE_ADDRESS, data, 2);
}

static void mpu6050_read_reg(uint8_t reg, uint8_t *buf, uint16_t length)
{
    uint8_t reg_buf[1] = {reg};

    IoTI2cWrite(MPU6050_I2C_PORT, MPU6050_SLAVE_ADDRESS, reg_buf, 1);
    IoTI2cRead(MPU6050_I2C_PORT, MPU6050_SLAVE_ADDRESS, buf, length);
}

void mpu6050_env_init(void)
{
    LOS_Msleep(100);
    mpu6050_write_reg(MPU6050_RA_PWR_MGMT_1, 0x80);
    LOS_Msleep(200);
    mpu6050_write_reg(MPU6050_RA_PWR_MGMT_1, 0x00);
    mpu6050_write_reg(MPU6050_RA_INT_ENABLE, 0x00);
    mpu6050_write_reg(MPU6050_RA_USER_CTRL, 0x00);
    mpu6050_write_reg(MPU6050_RA_FIFO_EN, 0x00);
    mpu6050_write_reg(MPU6050_RA_INT_PIN_CFG, 0x80);
    mpu6050_write_reg(MPU6050_RA_MOT_THR, 0x03);
    mpu6050_write_reg(MPU6050_RA_MOT_DUR, 0x14);
    mpu6050_write_reg(MPU6050_RA_CONFIG, 0x04);
    mpu6050_write_reg(MPU6050_RA_ACCEL_CONFIG, 0x1C);
    mpu6050_write_reg(MPU6050_RA_INT_PIN_CFG, 0x1C);
    mpu6050_write_reg(MPU6050_RA_INT_ENABLE, 0x40);
}

void mpu6050_env_read_accel(short *accel_xyz)
{
    uint8_t buf[6];

    if (accel_xyz == NULL) {
        return;
    }

    mpu6050_read_reg(MPU6050_ACC_OUT, buf, 6);
    accel_xyz[0] = (short)((buf[0] << 8) | buf[1]);
    accel_xyz[1] = (short)((buf[2] << 8) | buf[3]);
    accel_xyz[2] = (short)((buf[4] << 8) | buf[5]);
}

void mpu6050_env_read_gyro(short *gyro_xyz)
{
    uint8_t buf[6];

    if (gyro_xyz == NULL) {
        return;
    }

    mpu6050_read_reg(MPU6050_GYRO_OUT, buf, 6);
    gyro_xyz[0] = (short)((buf[0] << 8) | buf[1]);
    gyro_xyz[1] = (short)((buf[2] << 8) | buf[3]);
    gyro_xyz[2] = (short)((buf[4] << 8) | buf[5]);
}

void mpu6050_env_read_temp(short *temp_raw)
{
    uint8_t buf[2];

    if (temp_raw == NULL) {
        return;
    }

    mpu6050_read_reg(MPU6050_TEMP_OUT_H, buf, 2);
    *temp_raw = (short)((buf[0] << 8) | buf[1]);
}
