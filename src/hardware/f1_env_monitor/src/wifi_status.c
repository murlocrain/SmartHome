#include "env_monitor.h"
#include "wifi_config.h"

#include <string.h>
#include <stdio.h>

#include "los_task.h"
#include "config_network.h"
#include "lz_hardware.h"

static volatile bool g_wifi_connected = false;

bool wifi_monitor_is_connected(void)
{
    return g_wifi_connected;
}

void wifi_monitor_get_link(env_monitor_data_t *data)
{
    WifiLinkedInfo info;

    if (data == NULL) {
        return;
    }

    memset(&info, 0, sizeof(info));
    if (GetLinkedInfo(&info) != WIFI_SUCCESS) {
        data->wifi_conn_state = WIFI_DISCONNECTED;
        data->wifi_rssi = 0;
        data->wifi_ip = 0;
        data->wifi_band = 0;
        data->wifi_frequency = 0;
        return;
    }

    data->wifi_conn_state = (int)info.connState;
    data->wifi_rssi = info.rssi;
    data->wifi_ip = info.ipAddress;
    data->wifi_band = info.band;
    data->wifi_frequency = info.frequency;
}

static void wifi_update_link_state(void)
{
    WifiLinkedInfo info;

    memset(&info, 0, sizeof(info));
    if (GetLinkedInfo(&info) != WIFI_SUCCESS) {
        g_wifi_connected = false;
        return;
    }
    g_wifi_connected = (info.connState == WIFI_CONNECTED && info.ipAddress != 0);
}

static void wifi_monitor_task(void *arg)
{
    uint8_t mac_address[6] = {0x00, 0xdc, 0xb6, 0x90, 0x02, 0x00};
    char ssid[32] = ENV_MONITOR_WIFI_SSID;
    char password[32] = ENV_MONITOR_WIFI_PASSWORD;

    (void)arg;

    FlashInit();
    VendorSet(VENDOR_ID_WIFI_MODE, "STA", 3);
    VendorSet(VENDOR_ID_MAC, mac_address, 6);
    VendorSet(VENDOR_ID_WIFI_ROUTE_SSID, ssid, sizeof(ssid));
    VendorSet(VENDOR_ID_WIFI_ROUTE_PASSWD, password, sizeof(password));

    SetWifiModeOff();
    if (SetWifiModeOn() != 0) {
        printf("[env_monitor] WiFi STA start failed\n");
    }

    while (1) {
        wifi_update_link_state();
        LOS_Msleep(1000);
    }
}

void wifi_monitor_start(void)
{
    unsigned int thread_id;
    TSK_INIT_PARAM_S task = {0};
    unsigned int ret;

    task.pfnTaskEntry = (TSK_ENTRY_FUNC)wifi_monitor_task;
    task.uwStackSize = 4096;
    task.pcName = "env_wifi";
    task.usTaskPrio = 25;
    ret = LOS_TaskCreate(&thread_id, &task);
    if (ret != LOS_OK) {
        printf("[env_monitor] wifi task create failed: 0x%x\n", ret);
    }
}
