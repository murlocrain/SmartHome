#include "env_monitor.h"
#include "voice_ctrl.h"
#include "lcd.h"

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#define LCD_Y_TITLE     0
#define LCD_Y_LINE1    17
#define LCD_Y_SEC1     19
#define LCD_Y_MQ2      36
#define LCD_Y_SHT30    52
#define LCD_Y_BH1750   68
#define LCD_Y_LINE2    85
#define LCD_Y_SEC2     87
#define LCD_Y_ACCEL   104
#define LCD_Y_GYRO    120
#define LCD_Y_MPU_T   136
#define LCD_Y_LINE3   153
#define LCD_Y_PIR     155
#define LCD_Y_WIFI    171
#define LCD_Y_LINE4   188
#define LCD_Y_VOICE1  190
#define LCD_Y_VOICE2  206
#define LCD_Y_VOICE3  222

#define LCD_COL_LABEL   0
#define LCD_COL_VALUE  64

typedef struct {
    bool inited;
    float mq2_voltage_v;
    float temp_c;
    float humi_pct;
    float lux;
    float accel_g[3];
    float gyro_dps[3];
    float mpu_temp_c;
    int pir_gpio;
    int wifi_conn_state;
    unsigned int wifi_ip;
    int wifi_rssi;
} env_lcd_cache_t;

static env_lcd_cache_t g_lcd_cache;

void env_monitor_lcd_init(void)
{
    lcd_init();
    lcd_fill(0, 0, LCD_W, LCD_H, LCD_BLACK);
    memset(&g_lcd_cache, 0, sizeof(g_lcd_cache));
}

void env_monitor_lcd_load_ui(void)
{
    /* ── 标题（居中） ── */
    lcd_show_string(84, LCD_Y_TITLE, "RK2206 Env Monitor", LCD_YELLOW, LCD_BLACK, 16, 0);

    /* ── 环境传感器区域 ── */
    lcd_draw_line(0, LCD_Y_LINE1, LCD_W - 1, LCD_Y_LINE1, LCD_GREEN);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_SEC1, "[Sensors]", LCD_GREEN, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_MQ2, "MQ2", LCD_WHITE, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_SHT30, "T/H", LCD_WHITE, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_BH1750, "Lux", LCD_WHITE, LCD_BLACK, 16, 0);

    /* ── 运动传感器区域 ── */
    lcd_draw_line(0, LCD_Y_LINE2, LCD_W - 1, LCD_Y_LINE2, LCD_CYAN);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_SEC2, "[Motion]", LCD_CYAN, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_ACCEL, "Acc", LCD_WHITE, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_GYRO, "Gyro", LCD_WHITE, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_MPU_T, "MPU", LCD_WHITE, LCD_BLACK, 16, 0);

    /* ── 状态区域 ── */
    lcd_draw_line(0, LCD_Y_LINE3, LCD_W - 1, LCD_Y_LINE3, LCD_MAGENTA);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_PIR, "PIR", LCD_WHITE, LCD_BLACK, 16, 0);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_WIFI, "WiFi", LCD_WHITE, LCD_BLACK, 16, 0);

    /* ── 语音调试区域 ── */
    lcd_draw_line(0, LCD_Y_LINE4, LCD_W - 1, LCD_Y_LINE4, LCD_GRAY);
    lcd_show_string(LCD_COL_LABEL, LCD_Y_VOICE1, "VOICE", LCD_WHITE, LCD_BLACK, 16, 0);
}

void env_monitor_lcd_update(const env_monitor_data_t *data)
{
    char buf[32];

    if (data == NULL) {
        return;
    }

    if (!g_lcd_cache.inited || data->mq2_voltage_v != g_lcd_cache.mq2_voltage_v) {
        sprintf(buf, ":%4.2fV", data->mq2_voltage_v);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_MQ2, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        g_lcd_cache.mq2_voltage_v = data->mq2_voltage_v;
    }

    if (!g_lcd_cache.inited ||
        data->temp_c != g_lcd_cache.temp_c ||
        data->humi_pct != g_lcd_cache.humi_pct) {
        sprintf(buf, ":%.1f %.0f%%", data->temp_c, data->humi_pct);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_SHT30, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        g_lcd_cache.temp_c = data->temp_c;
        g_lcd_cache.humi_pct = data->humi_pct;
    }

    if (!g_lcd_cache.inited || data->lux != g_lcd_cache.lux) {
        sprintf(buf, ":%4.0f", data->lux);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_BH1750, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        g_lcd_cache.lux = data->lux;
    }

    if (!g_lcd_cache.inited ||
        data->accel_g[0] != g_lcd_cache.accel_g[0] ||
        data->accel_g[1] != g_lcd_cache.accel_g[1] ||
        data->accel_g[2] != g_lcd_cache.accel_g[2]) {
        sprintf(buf, ":%.1f,%.1f", data->accel_g[0], data->accel_g[1]);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_ACCEL, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        g_lcd_cache.accel_g[0] = data->accel_g[0];
        g_lcd_cache.accel_g[1] = data->accel_g[1];
        g_lcd_cache.accel_g[2] = data->accel_g[2];
    }

    if (!g_lcd_cache.inited ||
        data->gyro_dps[0] != g_lcd_cache.gyro_dps[0] ||
        data->gyro_dps[1] != g_lcd_cache.gyro_dps[1] ||
        data->gyro_dps[2] != g_lcd_cache.gyro_dps[2]) {
        sprintf(buf, ":%.0f,%.0f", data->gyro_dps[0], data->gyro_dps[1]);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_GYRO, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        g_lcd_cache.gyro_dps[0] = data->gyro_dps[0];
        g_lcd_cache.gyro_dps[1] = data->gyro_dps[1];
        g_lcd_cache.gyro_dps[2] = data->gyro_dps[2];
    }

    if (!g_lcd_cache.inited || data->mpu_temp_c != g_lcd_cache.mpu_temp_c) {
        sprintf(buf, ":%4.1f", data->mpu_temp_c);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_MPU_T, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        g_lcd_cache.mpu_temp_c = data->mpu_temp_c;
    }

    if (!g_lcd_cache.inited || data->pir_gpio != g_lcd_cache.pir_gpio) {
        if (data->pir_gpio != 0) {
            lcd_show_string(LCD_COL_VALUE, LCD_Y_PIR, ": YES", LCD_RED, LCD_BLACK, 16, 0);
        } else {
            lcd_show_string(LCD_COL_VALUE, LCD_Y_PIR, ": NO ", LCD_GREEN, LCD_BLACK, 16, 0);
        }
        g_lcd_cache.pir_gpio = data->pir_gpio;
    }

    if (!g_lcd_cache.inited ||
        data->wifi_conn_state != g_lcd_cache.wifi_conn_state ||
        data->wifi_ip != g_lcd_cache.wifi_ip ||
        data->wifi_rssi != g_lcd_cache.wifi_rssi) {
        if (data->wifi_conn_state == 1 && data->wifi_ip != 0) {
            sprintf(buf, ":%ddBm", data->wifi_rssi);
            lcd_show_string(LCD_COL_VALUE, LCD_Y_WIFI, (const uint8_t *)buf, LCD_WHITE, LCD_BLACK, 16, 0);
        } else {
            lcd_show_string(LCD_COL_VALUE, LCD_Y_WIFI, ": OFF ", LCD_RED, LCD_BLACK, 16, 0);
        }
        g_lcd_cache.wifi_conn_state = data->wifi_conn_state;
        g_lcd_cache.wifi_ip = data->wifi_ip;
        g_lcd_cache.wifi_rssi = data->wifi_rssi;
    }

    g_lcd_cache.inited = true;
}

/*
 * 语音调试信息 LCD 缓存
 */
typedef struct {
    bool inited;
    uint32_t uart_total_bytes;
    uint32_t voice_cmd_count;
    uint32_t unknown_cmd_count;
    uint32_t frame_crc_errors;
    uint32_t frame_len_errors;
    uint8_t  proto_mode;
    uint8_t  last_raw_len;
    uint8_t  last_raw[8];
    uint16_t last_cmd;
    uint8_t  last_cmd_matched;
    uint8_t  uart2_init_ok;
    uint8_t  voice_alive;
} voice_lcd_cache_t;

static voice_lcd_cache_t g_voice_lcd_cache;

void env_monitor_lcd_update_voice_debug(void)
{
    const voice_debug_t *dbg = &g_voice_debug;
    voice_lcd_cache_t *cache = &g_voice_lcd_cache;
    char buf[64];
    bool changed = false;

    if (!cache->inited ||
        cache->uart_total_bytes != dbg->uart_total_bytes ||
        cache->voice_cmd_count != dbg->voice_cmd_count ||
        cache->unknown_cmd_count != dbg->unknown_cmd_count ||
        cache->frame_crc_errors != dbg->frame_crc_errors ||
        cache->frame_len_errors != dbg->frame_len_errors ||
        cache->proto_mode != dbg->proto_mode ||
        cache->last_raw_len != dbg->last_raw_len ||
        memcmp(cache->last_raw, dbg->last_raw, sizeof(cache->last_raw)) != 0 ||
        cache->last_cmd != dbg->last_cmd ||
        cache->last_cmd_matched != dbg->last_cmd_matched ||
        cache->uart2_init_ok != dbg->uart2_init_ok ||
        cache->voice_alive != dbg->voice_task_alive) {
        changed = true;
    }

    if (!changed) return;

    cache->uart_total_bytes = dbg->uart_total_bytes;
    cache->voice_cmd_count = dbg->voice_cmd_count;
    cache->unknown_cmd_count = dbg->unknown_cmd_count;
    cache->frame_crc_errors = dbg->frame_crc_errors;
    cache->frame_len_errors = dbg->frame_len_errors;
    cache->proto_mode = dbg->proto_mode;
    cache->last_raw_len = dbg->last_raw_len;
    memcpy(cache->last_raw, dbg->last_raw, sizeof(cache->last_raw));
    cache->last_cmd = dbg->last_cmd;
    cache->last_cmd_matched = dbg->last_cmd_matched;
    cache->uart2_init_ok = dbg->uart2_init_ok;
    cache->voice_alive = dbg->voice_task_alive;
    cache->inited = true;

    /* ── 行1: VOICE 状态概览 ── */
    if (dbg->uart_total_bytes == 0) {
        snprintf(buf, sizeof(buf), ":NO DATA (check wire)");
        lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE1, (const uint8_t *)buf, LCD_RED, LCD_BLACK, 16, 0);
    } else {
        const char *pmode = (dbg->proto_mode == 2) ? "AA" :
                            (dbg->proto_mode == 1) ? "RAW" : "?";
        snprintf(buf, sizeof(buf), ":%uB %s ok:%u",
                 (unsigned)dbg->uart_total_bytes, pmode,
                 (unsigned)dbg->voice_cmd_count);
        lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE1, (const uint8_t *)buf, LCD_GREEN, LCD_BLACK, 16, 0);
    }

    /* ── 行2: 最近命令码 & 原始 hex ── */
    if (dbg->last_raw_len > 0 || dbg->last_cmd != 0) {
        char hex[25] = {0};
        int hpos = 0;
        int k;
        for (k = 0; k < dbg->last_raw_len && k < 8; k++)
            hpos += snprintf(hex + hpos, sizeof(hex) - hpos, "%02X", dbg->last_raw[k]);
        if (dbg->last_cmd_matched) {
            snprintf(buf, sizeof(buf), ":0x%04X OK %s", dbg->last_cmd, hex);
            lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE2, (const uint8_t *)buf, LCD_GREEN, LCD_BLACK, 16, 0);
        } else if (dbg->last_cmd != 0) {
            snprintf(buf, sizeof(buf), ":0x%04X ?? %s", dbg->last_cmd, hex);
            lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE2, (const uint8_t *)buf, LCD_RED, LCD_BLACK, 16, 0);
        } else {
            snprintf(buf, sizeof(buf), ":RAW %s", hex);
            lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE2, (const uint8_t *)buf, LCD_CYAN, LCD_BLACK, 16, 0);
        }
    } else {
        lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE2, ":waiting...", LCD_GRAY, LCD_BLACK, 16, 0);
    }

    /* ── 行3: 通信错误统计（校验/长度错误/未知码） ── */
    if (dbg->frame_crc_errors > 0 || dbg->frame_len_errors > 0 ||
        dbg->unknown_cmd_count > 0) {
        snprintf(buf, sizeof(buf), ":err CRC:%u unk:%u",
                 (unsigned)dbg->frame_crc_errors,
                 (unsigned)dbg->unknown_cmd_count);
        int color = (dbg->frame_crc_errors > 0) ? LCD_RED : LCD_YELLOW;
        lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE3, (const uint8_t *)buf, color, LCD_BLACK, 16, 0);
    } else if (dbg->uart_total_bytes > 0) {
        snprintf(buf, sizeof(buf), ":no errors");
        lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE3, (const uint8_t *)buf, LCD_GREEN, LCD_BLACK, 16, 0);
    } else {
        lcd_show_string(LCD_COL_VALUE, LCD_Y_VOICE3, (const uint8_t *)"", LCD_BLACK, LCD_BLACK, 16, 0);
    }
}
