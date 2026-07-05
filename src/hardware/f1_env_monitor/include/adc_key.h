#ifndef __ADC_KEY_H__
#define __ADC_KEY_H__

#include <stdint.h>

/* ADC 电阻分压对应 b3_adc_key：K3≈0.01V K5≈1.65V K6≈0.55V */
#define KEY_RELEASE 0x00
#define KEY_K3      0x01   /* UP 区，约 10mV */
#define KEY_K4      0x02   /* DOWN 区，约 1.0V */
#define KEY_K5      0x04   /* LEFT 区，约 1.65V */
#define KEY_K6      0x08   /* RIGHT 区，约 0.55V */

void adc_key_start(void);

#endif
