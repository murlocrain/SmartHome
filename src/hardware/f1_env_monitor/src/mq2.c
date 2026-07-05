#include "mq2.h"

#include <stdio.h>

#include "iot_errno.h"
#include "iot_adc.h"

#define MQ2_ADC_CHANNEL 4

unsigned int mq2_dev_init(void)
{
    if (IoTAdcInit(MQ2_ADC_CHANNEL) != IOT_SUCCESS) {
        printf("[mq2] ADC init fail\n");
        return 1;
    }
    return 0;
}

unsigned int mq2_read_adc_raw(void)
{
    unsigned int data = 0;

    if (IoTAdcGetVal(MQ2_ADC_CHANNEL, &data) != IOT_SUCCESS) {
        return 0;
    }
    return data;
}
