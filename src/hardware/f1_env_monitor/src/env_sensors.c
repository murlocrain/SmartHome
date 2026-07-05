#include "env_monitor.h"
#include "env_convert.h"
#include "mq2.h"
#include "mpu6050.h"

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#include "iot_errno.h"
#include "iot_i2c.h"
#include "iot_gpio.h"
#include "iot_adc.h"
#include "los_task.h"

#define I2C_HANDLE          EI2C0_M2
#define UART_RX_FIFO_SIZE   256
#define UART_REPORT_MAX     8
#define SHT30_I2C_ADDRESS   0x44
#define BH1750_I2C_ADDRESS  0x23
#define GPIO_BODY_INDUCTION GPIO0_PA3
#define KEY_ADC_CHANNEL     7

typedef struct {
    int max;
    int read;
    int write;
    uint8_t buffer[UART_RX_FIFO_SIZE];
} uart_rx_fifo_t;

static uart_rx_fifo_t g_uart_report_fifo;

static void uart_fifo_init(uart_rx_fifo_t *fifo)
{
    fifo->max = UART_RX_FIFO_SIZE;
    fifo->read = 0;
    fifo->write = 0;
}

static int uart_fifo_is_empty(const uart_rx_fifo_t *fifo)
{
    return fifo->write == fifo->read;
}

static int uart_fifo_is_full(const uart_rx_fifo_t *fifo)
{
    return ((fifo->write + 1) % fifo->max) == fifo->read;
}

static void uart_fifo_write(uart_rx_fifo_t *fifo, const uint8_t *data, int len)
{
    int i;

    for (i = 0; i < len; i++) {
        if (uart_fifo_is_full(fifo)) {
            break;
        }
        fifo->buffer[fifo->write] = data[i];
        fifo->write = (fifo->write + 1) % fifo->max;
    }
}

static int uart_fifo_read(uart_rx_fifo_t *fifo, uint8_t *data, int len)
{
    int i;

    for (i = 0; i < len; i++) {
        if (uart_fifo_is_empty(fifo)) {
            break;
        }
        data[i] = fifo->buffer[fifo->read];
        fifo->read = (fifo->read + 1) % fifo->max;
    }
    return i;
}

static void sht30_read_raw(uint16_t *temp_raw, uint16_t *humi_raw)
{
    uint8_t buf[6] = {0};
    uint8_t cmd[2] = {0xE0, 0x00};

    if (temp_raw == NULL || humi_raw == NULL) {
        return;
    }

    IoTI2cWrite(I2C_HANDLE, SHT30_I2C_ADDRESS, cmd, 2);
    IoTI2cRead(I2C_HANDLE, SHT30_I2C_ADDRESS, buf, 6);
    *temp_raw = (uint16_t)((buf[0] << 8) | buf[1]);
    *humi_raw = (uint16_t)((buf[3] << 8) | buf[4]);
}

static void bh1750_read_raw(uint16_t *raw)
{
    uint8_t recv[2] = {0};

    if (raw == NULL) {
        return;
    }

    IoTI2cRead(I2C_HANDLE, BH1750_I2C_ADDRESS, recv, 2);
    *raw = (uint16_t)((recv[0] << 8) | recv[1]);
}

static int pir_gpio_read(void)
{
    IotGpioValue value = IOT_GPIO_VALUE0;

    IoTGpioGetInputVal(GPIO_BODY_INDUCTION, &value);
    return (int)value;
}

static unsigned int key_adc_read_raw(void)
{
    unsigned int data = 0;

    if (IoTAdcGetVal(KEY_ADC_CHANNEL, &data) != IOT_SUCCESS) {
        return 0;
    }
    return data;
}

static void uart2_read_raw(uint8_t *buf, uint8_t buf_len, uint8_t *out_len)
{
    int len;

    if (buf == NULL || out_len == NULL || buf_len == 0) {
        return;
    }

    memset(buf, 0, buf_len);
    len = uart_fifo_read(&g_uart_report_fifo, buf, UART_REPORT_MAX);
    if (len > (int)buf_len) {
        len = (int)buf_len;
    }
    *out_len = (uint8_t)len;
}

void env_sensors_init(void)
{
    uint8_t sht30_cmd[2] = {0x22, 0x36};
    uint8_t bh1750_cmd[1] = {0x10};

    IoTI2cInit(I2C_HANDLE, EI2C_FRE_400K);
    IoTI2cWrite(I2C_HANDLE, SHT30_I2C_ADDRESS, sht30_cmd, 2);
    IoTI2cWrite(I2C_HANDLE, BH1750_I2C_ADDRESS, bh1750_cmd, 1);
    mpu6050_env_init();
    mq2_dev_init();
    IoTAdcInit(KEY_ADC_CHANNEL);
    uart_fifo_init(&g_uart_report_fifo);

    IoTGpioInit(GPIO_BODY_INDUCTION);
    IoTGpioSetDir(GPIO_BODY_INDUCTION, IOT_GPIO_DIR_IN);
}

void env_sensors_read(env_monitor_data_t *data)
{
    if (data == NULL) {
        return;
    }

    data->mq2_adc = mq2_read_adc_raw();
    sht30_read_raw(&data->sht30_temp_raw, &data->sht30_humi_raw);
    bh1750_read_raw(&data->bh1750_raw);
    mpu6050_env_read_accel(data->accel);
    mpu6050_env_read_gyro(data->gyro);
    mpu6050_env_read_temp(&data->mpu_temp_raw);
    data->pir_gpio = pir_gpio_read();
    data->key_adc = key_adc_read_raw();
    uart2_read_raw(data->uart_rx, sizeof(data->uart_rx), &data->uart_rx_len);
    wifi_monitor_get_link(data);
    env_monitor_apply_units(data);
}

/*
 * voice_ctrl 将收到的字节喂入 report FIFO，供 env_sensors_read()
 * 读取后上报到 [env] 日志的 uart:N 字段。
 */
void env_sensors_feed_uart_report(const uint8_t *buf, int len)
{
    if (buf == NULL || len <= 0) {
        return;
    }
    uart_fifo_write(&g_uart_report_fifo, buf, len);
}
