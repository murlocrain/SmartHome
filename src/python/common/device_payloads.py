from common.models import EnvMonitorData


def build_realtime_data(record: EnvMonitorData) -> dict:
    wifi_connected = record.wifi_conn_state == 1 if record.wifi_conn_state is not None else False
    light_on = (record.lightStatus or "").upper() == "ON"
    motor_on = (record.motorStatus or "").upper() == "ON"
    pir_detected = record.pir_gpio == 1 if record.pir_gpio is not None else False

    return {
        "temperature": record.sht30_temp_raw,
        "humidity": record.sht30_humi_raw,
        "light": record.bh1750_raw,
        "smoke": record.mq2_adc,
        "pir": pir_detected,
        "wifi": wifi_connected,
        "wifi_rssi": record.wifi_rssi,
        "lightStatus": light_on,
        "motorStatus": motor_on,
        "ip": record.wifi_ip,
        "voice_command": record.uart_rx_hex,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
    }
