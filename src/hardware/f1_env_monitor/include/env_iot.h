#ifndef __ENV_IOT_H__
#define __ENV_IOT_H__

#include "env_monitor.h"

void env_iot_start(void);
unsigned int env_iot_is_connected(void);
void env_iot_publish(const env_monitor_data_t *data);
void env_iot_publish_status(void);

#endif
