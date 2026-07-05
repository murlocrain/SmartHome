#include "env_iot.h"
#include "env_control.h"
#include "env_event.h"
#include "iot_config.h"

#include <stddef.h>
#include <stdio.h>
#include <string.h>

#include "MQTTClient.h"
#include "cJSON.h"
#include "config_network.h"
#include "drv_light.h"
#include "drv_motor.h"
#include "los_task.h"

#define MAX_BUFFER_LENGTH 2048

static unsigned char g_send_buf[MAX_BUFFER_LENGTH];
static unsigned char g_read_buf[MAX_BUFFER_LENGTH];

static Network g_network;
static MQTTClient g_client;
static unsigned int g_mqtt_connected = 0;

static char g_publish_topic[128];
static char g_subscribe_topic[128];
static char g_response_topic[128];

static void env_iot_send_cmd_event(int cmd)
{
    env_event_t event = {0};

    event.event = env_event_iot_cmd;
    event.iot_cmd = cmd;
    event.param = 0;
    env_event_send(&event);
}

static void env_iot_send_cmd_event_ex(int cmd, int param)
{
    env_event_t event = {0};

    event.event = env_event_iot_cmd;
    event.iot_cmd = cmd;
    event.param = param;
    env_event_send(&event);
}

static void env_iot_set_onoff(cJSON *root, const char *field, int on_cmd, int off_cmd)
{
    cJSON *para_obj = NULL;
    cJSON *status_obj = NULL;
    char *value = NULL;

    para_obj = cJSON_GetObjectItem(root, "paras");
    if (para_obj == NULL) {
        return;
    }
    status_obj = cJSON_GetObjectItem(para_obj, field);
    if (status_obj == NULL) {
        return;
    }
    value = cJSON_GetStringValue(status_obj);
    if (value == NULL) {
        return;
    }
    if (!strcmp(value, "ON")) {
        env_iot_send_cmd_event(on_cmd);
    } else if (!strcmp(value, "OFF")) {
        env_iot_send_cmd_event(off_cmd);
    }
}

static void env_iot_light_control(cJSON *root)
{
    cJSON *para_obj = NULL;
    cJSON *item = NULL;
    char *str_val = NULL;
    int int_val = 0;
    bool has_para = false;

    para_obj = cJSON_GetObjectItem(root, "paras");
    if (para_obj == NULL) {
        return;
    }

    item = cJSON_GetObjectItem(para_obj, "onoff");
    if (item != NULL) {
        str_val = cJSON_GetStringValue(item);
        if (str_val != NULL) {
            if (!strcmp(str_val, "ON")) {
                env_iot_send_cmd_event(ENV_CMD_LIGHT_ON);
                has_para = true;
            } else if (!strcmp(str_val, "OFF")) {
                env_iot_send_cmd_event(ENV_CMD_LIGHT_OFF);
                has_para = true;
            }
        }
    }

    item = cJSON_GetObjectItem(para_obj, "brightness");
    if (item != NULL && cJSON_IsNumber(item)) {
        int_val = cJSON_GetNumberValue(item);
        if (int_val >= LIGHT_BRIGHTNESS_MIN && int_val <= LIGHT_BRIGHTNESS_MAX) {
            env_iot_send_cmd_event_ex(ENV_CMD_LIGHT_BRIGHTNESS, int_val);
            has_para = true;
        }
    }

    item = cJSON_GetObjectItem(para_obj, "color");
    if (item != NULL) {
        if (cJSON_IsNumber(item)) {
            int_val = cJSON_GetNumberValue(item);
            if (int_val >= 0 && int_val < LIGHT_COLOR_MAX) {
                env_iot_send_cmd_event(0x100 + int_val);
                has_para = true;
            }
        } else if (cJSON_IsString(item)) {
            str_val = cJSON_GetStringValue(item);
            if (str_val != NULL) {
                if (!strcmp(str_val, "WHITE") || !strcmp(str_val, "white")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_WHITE);
                else if (!strcmp(str_val, "RED") || !strcmp(str_val, "red")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_RED);
                else if (!strcmp(str_val, "GREEN") || !strcmp(str_val, "green")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_GREEN);
                else if (!strcmp(str_val, "BLUE") || !strcmp(str_val, "blue")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_BLUE);
                else if (!strcmp(str_val, "YELLOW") || !strcmp(str_val, "yellow")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_YELLOW);
                else if (!strcmp(str_val, "CYAN") || !strcmp(str_val, "cyan")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_CYAN);
                else if (!strcmp(str_val, "PURPLE") || !strcmp(str_val, "purple")) env_iot_send_cmd_event(0x100 + LIGHT_COLOR_PURPLE);
                has_para = true;
            }
        }
    }

    item = cJSON_GetObjectItem(para_obj, "level");
    if (item != NULL) {
        if (cJSON_IsNumber(item)) {
            int_val = cJSON_GetNumberValue(item);
            if (int_val >= LIGHT_LEVEL_MIN && int_val <= LIGHT_LEVEL_MAX) {
                env_iot_send_cmd_event(0x200 + int_val);
                has_para = true;
            }
        }
    }

    item = cJSON_GetObjectItem(para_obj, "mode");
    if (item != NULL) {
        if (cJSON_IsNumber(item)) {
            int_val = cJSON_GetNumberValue(item);
            if (int_val >= 0 && int_val < LIGHT_MODE_MAX) {
                env_iot_send_cmd_event(0x300 + int_val);
                has_para = true;
            }
        } else if (cJSON_IsString(item)) {
            str_val = cJSON_GetStringValue(item);
            if (str_val != NULL) {
                if (!strcmp(str_val, "STATIC") || !strcmp(str_val, "static")) env_iot_send_cmd_event(0x300 + LIGHT_MODE_STATIC);
                else if (!strcmp(str_val, "BREATH") || !strcmp(str_val, "breath")) env_iot_send_cmd_event(0x300 + LIGHT_MODE_BREATH);
                has_para = true;
            }
        }
    }

    if (!has_para) {
        env_iot_send_cmd_event(ENV_CMD_LIGHT_ON);
    }
}

static void env_iot_send_cmd_response(const char *request_id, int result_code,
                                      const char *result_msg)
{
    MQTTMessage rsp_msg;
    char rsp_topic[200];
    char rsp_payload[256];
    int rc;

    sprintf(rsp_topic, "%s/request_id=%s", g_response_topic, request_id);
    sprintf(rsp_payload,
            "{\"result_code\":%d,\"response_name\":\"COMMAND_RESPONSE\","
            "\"paras\":{\"result\":\"%s\"}}",
            result_code, result_msg);

    rsp_msg.qos = 0;
    rsp_msg.retained = 0;
    rsp_msg.payload = rsp_payload;
    rsp_msg.payloadlen = strlen(rsp_payload);

    rc = MQTTPublish(&g_client, rsp_topic, &rsp_msg);
    if (rc != 0) {
        printf("[env_iot] cmd response FAIL rc=%d topic=%s\n", rc, rsp_topic);
    } else {
        printf("[env_iot] cmd response OK   topic=%s\n", rsp_topic);
    }
}

static void env_iot_mqtt_message_arrived(MessageData *data)
{
    cJSON *root = NULL;
    cJSON *cmd_name = NULL;
    char *cmd_name_str = NULL;
    char *request_id_idx = NULL;
    char request_id[40] = {0};

    printf("[env_iot] cmd topic %.*s payload %.*s\n",
           data->topicName->lenstring.len, data->topicName->lenstring.data,
           data->message->payloadlen, (char *)data->message->payload);

    /* 提取 request_id */
    request_id_idx = strstr(data->topicName->lenstring.data, "request_id=");
    if (request_id_idx != NULL) {
        strncpy(request_id, request_id_idx + 11, sizeof(request_id) - 1);
        request_id[sizeof(request_id) - 1] = '\0';
    }

    root = cJSON_ParseWithLength(data->message->payload, data->message->payloadlen);
    if (root == NULL) {
        env_iot_send_cmd_response(request_id, 1, "parse_error");
        return;
    }

    cmd_name = cJSON_GetObjectItem(root, "command_name");
    if (cmd_name == NULL) {
        env_iot_send_cmd_response(request_id, 1, "missing_command_name");
        cJSON_Delete(root);
        return;
    }

    cmd_name_str = cJSON_GetStringValue(cmd_name);
    if (cmd_name_str == NULL) {
        env_iot_send_cmd_response(request_id, 1, "invalid_command_name");
        cJSON_Delete(root);
        return;
    }

    /* 识别并分发命令 */
    if (!strcmp(cmd_name_str, "light_control")) {
        env_iot_light_control(root);
    } else if (!strcmp(cmd_name_str, "motor_control")) {
        env_iot_set_onoff(root, "onoff", ENV_CMD_MOTOR_ON, ENV_CMD_MOTOR_OFF);
        {
            cJSON *para_obj = cJSON_GetObjectItem(root, "paras");
            cJSON *speed = NULL;
            if (para_obj != NULL) {
                speed = cJSON_GetObjectItem(para_obj, "speed");
            }
            if (speed != NULL && cJSON_IsNumber(speed)) {
                int val = cJSON_GetNumberValue(speed);
                if (val >= 0 && val <= 100) {
                    env_iot_send_cmd_event_ex(ENV_CMD_MOTOR_SPEED, val);
                }
            }
        }
    } else if (!strcmp(cmd_name_str, "beep_play")) {
        cJSON *para_obj = cJSON_GetObjectItem(root, "paras");
        cJSON *dur_item = NULL;
        cJSON *freq_item = NULL;
        int duration = 0;
        int freq_hz = 0;
        int has_dur = 0;
        int has_freq = 0;

        if (para_obj != NULL) {
            dur_item = cJSON_GetObjectItem(para_obj, "duration");
            if (dur_item != NULL && cJSON_IsNumber(dur_item)) {
                duration = cJSON_GetNumberValue(dur_item);
                has_dur = 1;
            }
            freq_item = cJSON_GetObjectItem(para_obj, "frequency");
            if (freq_item != NULL && cJSON_IsNumber(freq_item)) {
                freq_hz = cJSON_GetNumberValue(freq_item);
                has_freq = 1;
            }
        }

        if (has_dur || has_freq) {
            int param;
            if (!has_freq) freq_hz = 800;
            if (!has_dur) duration = 2000;
            param = ((freq_hz & 0xFFFF) << 16) | (duration & 0xFFFF);
            env_iot_send_cmd_event_ex(ENV_CMD_BEEP_TONE, param);
        } else {
            env_iot_send_cmd_event(ENV_CMD_BEEP_PLAY);
        }
    } else if (!strcmp(cmd_name_str, "beep_song")) {
        cJSON *para_obj = cJSON_GetObjectItem(root, "paras");
        if (para_obj != NULL) {
            cJSON *id_item = cJSON_GetObjectItem(para_obj, "id");
            if (id_item != NULL && cJSON_IsNumber(id_item)) {
                int song_id = cJSON_GetNumberValue(id_item);
                env_iot_send_cmd_event_ex(ENV_CMD_BEEP_SONG, song_id);
            }
        }
    } else if (!strcmp(cmd_name_str, "beep_stop")) {
        env_iot_send_cmd_event(ENV_CMD_BEEP_STOP);
    } else {
        env_iot_send_cmd_response(request_id, 1, "unknown_command");
        cJSON_Delete(root);
        return;
    }

    /* 命令已分发，回应成功 */
    env_iot_send_cmd_response(request_id, 0, "success");
    cJSON_Delete(root);
}

void env_iot_publish(const env_monitor_data_t *data)
{
    int rc;
    MQTTMessage message;
    char payload[MAX_BUFFER_LENGTH] = {0};
    char uart_hex[40] = {0};
    unsigned int i;

    if (data == NULL || g_mqtt_connected == 0) {
        return;
    }

    if (data->uart_rx_len > 0) {
        for (i = 0; i < data->uart_rx_len && i < 8; i++) {
            sprintf(uart_hex + (i * 2), "%02X", data->uart_rx[i]);
        }
    } else {
        /* 华为云空字符串显示为 "-"，本周期无 UART 数据时上报占位 hex */
        strcpy(uart_hex, "00");
    }

    cJSON *root = cJSON_CreateObject();
    if (root == NULL) {
        return;
    }

    cJSON *serv_arr = cJSON_AddArrayToObject(root, "services");
    cJSON *arr_item = cJSON_CreateObject();
    cJSON_AddStringToObject(arr_item, "service_id", IOT_SERVICE_ID);
    cJSON *pro_obj = cJSON_CreateObject();
    cJSON_AddItemToObject(arr_item, "properties", pro_obj);

    /* 属性名保持与产品模型一致，数值为换算后的常用单位 */
    cJSON_AddNumberToObject(pro_obj, "mq2_adc", (int)(data->mq2_voltage_v * 1000.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "sht30_temp_raw", (double)data->temp_c);
    cJSON_AddNumberToObject(pro_obj, "sht30_humi_raw", (double)data->humi_pct);
    cJSON_AddNumberToObject(pro_obj, "bh1750_raw", (int)(data->lux + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "accel_x", (int)(data->accel_g[0] * 1000.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "accel_y", (int)(data->accel_g[1] * 1000.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "accel_z", (int)(data->accel_g[2] * 1000.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "gyro_x", (int)(data->gyro_dps[0] * 10.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "gyro_y", (int)(data->gyro_dps[1] * 10.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "gyro_z", (int)(data->gyro_dps[2] * 10.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "mpu_temp_raw", (double)data->mpu_temp_c);
    cJSON_AddNumberToObject(pro_obj, "pir_gpio", data->pir_gpio);
    if (data->pir_gpio != 0) {
        cJSON_AddStringToObject(pro_obj, "body_state", "有人");
    } else {
        cJSON_AddStringToObject(pro_obj, "body_state", "无人");
    }
    cJSON_AddNumberToObject(pro_obj, "key_adc", (int)(data->key_voltage_v * 1000.0f + 0.5f));
    cJSON_AddNumberToObject(pro_obj, "uart_rx_len", data->uart_rx_len);
    cJSON_AddStringToObject(pro_obj, "uart_rx_hex", uart_hex);
    cJSON_AddNumberToObject(pro_obj, "wifi_conn_state", data->wifi_conn_state);
    if (data->wifi_conn_state == 1 && data->wifi_ip != 0) {
        cJSON_AddStringToObject(pro_obj, "wifi_state", "已连接");
    } else {
        cJSON_AddStringToObject(pro_obj, "wifi_state", "未连接");
    }
    cJSON_AddNumberToObject(pro_obj, "wifi_rssi", data->wifi_rssi);
    cJSON_AddNumberToObject(pro_obj, "wifi_ip", data->wifi_ip);
    cJSON_AddNumberToObject(pro_obj, "wifi_band", data->wifi_band);
    cJSON_AddNumberToObject(pro_obj, "wifi_frequency", data->wifi_frequency);

    if (get_light_state()) {
        cJSON_AddStringToObject(pro_obj, "light_status", "ON");
    } else {
        cJSON_AddStringToObject(pro_obj, "light_status", "OFF");
    }
    if (get_motor_state()) {
        cJSON_AddStringToObject(pro_obj, "motor_status", "ON");
    } else {
        cJSON_AddStringToObject(pro_obj, "motor_status", "OFF");
    }

    cJSON_AddItemToArray(serv_arr, arr_item);

    char *payload_str = cJSON_PrintUnformatted(root);
    if (payload_str == NULL) {
        printf("[env_iot] cJSON_Print failed\n");
        cJSON_Delete(root);
        return;
    }
    strncpy(payload, payload_str, sizeof(payload) - 1);
    payload[sizeof(payload) - 1] = '\0';
    cJSON_free(payload_str);
    cJSON_Delete(root);

    if (payload[0] == '\0') {
        printf("[env_iot] empty payload, skip publish\n");
        return;
    }

    message.qos = 0;
    message.retained = 0;
    message.payload = payload;
    message.payloadlen = strlen(payload);

    printf("[env_iot] publish topic: %s\n", g_publish_topic);
    printf("[env_iot] publish len=%u\n", (unsigned)message.payloadlen);
    printf("[env_iot] publish body: %s\n", payload);

    rc = MQTTPublish(&g_client, g_publish_topic, &message);
    if (rc != 0) {
        printf("[env_iot] publish failed rc=%d (buf=%d, check MQTT send buffer)\n",
               rc, MAX_BUFFER_LENGTH);
        g_mqtt_connected = 0;
    } else {
        printf("[env_iot] publish ok\n");
    }
}

void env_iot_publish_status(void)
{
    int rc;
    MQTTMessage message;
    char payload[MAX_BUFFER_LENGTH] = {0};

    if (g_mqtt_connected == 0) {
        return;
    }

    cJSON *root = cJSON_CreateObject();
    if (root == NULL) {
        return;
    }

    cJSON *serv_arr = cJSON_AddArrayToObject(root, "services");
    cJSON *arr_item = cJSON_CreateObject();
    cJSON_AddStringToObject(arr_item, "service_id", IOT_SERVICE_ID);
    cJSON *pro_obj = cJSON_CreateObject();
    cJSON_AddItemToObject(arr_item, "properties", pro_obj);

    if (get_light_state()) {
        cJSON_AddStringToObject(pro_obj, "light_status", "ON");
    } else {
        cJSON_AddStringToObject(pro_obj, "light_status", "OFF");
    }
    if (get_motor_state()) {
        cJSON_AddStringToObject(pro_obj, "motor_status", "ON");
    } else {
        cJSON_AddStringToObject(pro_obj, "motor_status", "OFF");
    }

    cJSON_AddItemToArray(serv_arr, arr_item);

    char *payload_str = cJSON_PrintUnformatted(root);
    if (payload_str == NULL) {
        cJSON_Delete(root);
        return;
    }
    strncpy(payload, payload_str, sizeof(payload) - 1);
    payload[sizeof(payload) - 1] = '\0';
    cJSON_free(payload_str);
    cJSON_Delete(root);

    message.qos = 0;
    message.retained = 0;
    message.payload = payload;
    message.payloadlen = strlen(payload);

    printf("[env_iot] publish status: %s\n", payload);
    rc = MQTTPublish(&g_client, g_publish_topic, &message);
    if (rc != 0) {
        printf("[env_iot] status publish failed rc=%d\n", rc);
        g_mqtt_connected = 0;
    } else {
        printf("[env_iot] status publish ok\n");
    }
}

unsigned int env_iot_is_connected(void)
{
    return g_mqtt_connected;
}

static int env_iot_mqtt_connect(void)
{
    int rc;

    NetworkInit(&g_network);
    printf("[env_iot] connect %s:%d\n", IOT_HOST, IOT_PORT);
    rc = NetworkConnect(&g_network, IOT_HOST, IOT_PORT);
    if (rc != 0) {
        printf("[env_iot] NetworkConnect failed: %d\n", rc);
        return -1;
    }

    MQTTClientInit(&g_client, &g_network, 2000, g_send_buf, sizeof(g_send_buf),
                   g_read_buf, sizeof(g_read_buf));

    MQTTString clientId = MQTTString_initializer;
    clientId.cstring = IOT_CLIENT_ID;

    MQTTString userName = MQTTString_initializer;
    userName.cstring = IOT_DEVICE_ID;

    MQTTString password = MQTTString_initializer;
    password.cstring = IOT_PASSWORD;

    MQTTPacket_connectData conn_data = MQTTPacket_connectData_initializer;
    conn_data.clientID = clientId;
    conn_data.username = userName;
    conn_data.password = password;
    conn_data.willFlag = 0;
    conn_data.MQTTVersion = 4;
    conn_data.keepAliveInterval = 60;
    conn_data.cleansession = 1;

    rc = MQTTConnect(&g_client, &conn_data);
    if (rc != 0) {
        printf("[env_iot] MQTTConnect failed: %d\n", rc);
        NetworkDisconnect(&g_network);
        MQTTDisconnect(&g_client);
        return -1;
    }

    sprintf(g_publish_topic, "$oc/devices/%s/sys/properties/report", IOT_DEVICE_ID);
    sprintf(g_subscribe_topic, "$oc/devices/%s/sys/commands/#", IOT_DEVICE_ID);
    sprintf(g_response_topic, "$oc/devices/%s/sys/commands/response", IOT_DEVICE_ID);

    rc = MQTTSubscribe(&g_client, g_subscribe_topic, 0, env_iot_mqtt_message_arrived);
    if (rc != 0) {
        printf("[env_iot] MQTTSubscribe failed: %d\n", rc);
        NetworkDisconnect(&g_network);
        MQTTDisconnect(&g_client);
        return -1;
    }

    g_mqtt_connected = 1;
    printf("[env_iot] MQTT connected, subscribed commands\n");
    return 0;
}

static void env_iot_task(void *arg)
{
    (void)arg;

    while (1) {
        if (!wifi_monitor_is_connected()) {
            g_mqtt_connected = 0;
            LOS_Msleep(1000);
            continue;
        }

        if (g_mqtt_connected == 0) {
            if (env_iot_mqtt_connect() != 0) {
                LOS_Msleep(3000);
                continue;
            }
        }

        if (MQTTYield(&g_client, 1000) != 0) {
            g_mqtt_connected = 0;
            NetworkDisconnect(&g_network);
            MQTTDisconnect(&g_client);
        }

        LOS_Msleep(100);
    }
}

void env_iot_start(void)
{
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};
    unsigned int ret;

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)env_iot_task;
    task.uwStackSize = 12288;
    task.pcName = "env_iot";
    task.usTaskPrio = 23;
    ret = LOS_TaskCreate(&thread_id, &task);
    if (ret != LOS_OK) {
        printf("[env_iot] task create failed: 0x%x\n", ret);
    }
}
