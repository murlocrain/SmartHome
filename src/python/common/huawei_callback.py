from datetime import datetime, timezone

from sqlalchemy.orm import Session

from common.config import logger
from common.models import Device, EnvMonitorData


def parse_huawei_callback_data(notify_data: dict) -> dict:
    body = {}
    services = notify_data.get("body", {}).get("services", [])

    if isinstance(services, dict):
        services = [services]

    for service in services:
        props = service.get("properties", {})
        for key, value in props.items():
            if isinstance(value, dict):
                body[key] = value.get("value")
            else:
                body[key] = value

    if not body and "body" in notify_data:
        raw_body = notify_data.get("body")
        if isinstance(raw_body, dict):
            for key, value in raw_body.items():
                if isinstance(value, dict):
                    body[key] = value.get("value")
                else:
                    body[key] = value

    return body


def _int_or_none(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _float_or_none(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _str_or_none(value):
    return str(value) if value is not None else None


def store_env_data(db: Session, device_id: str, body: dict, raw_data: dict) -> EnvMonitorData:
    device_record = db.query(Device).filter(Device.device_id == device_id).first()
    family_id = device_record.family_id if device_record else 1
    room_id = device_record.room_id if device_record else None

    if device_record:
        was_offline = not device_record.is_online
        device_record.is_online = True
        device_record.last_seen = datetime.now(timezone.utc)
        if was_offline:
            logger.info(f"设备上线: device={device_id}")
    else:
        logger.warning(f"回调设备不在Device表中: device={device_id}")

    data = EnvMonitorData(
        device_id=device_id,
        family_id=family_id,
        room_id=room_id,
        mq2_adc=_int_or_none(body.get("mq2_adc")),
        sht30_temp_raw=_float_or_none(body.get("sht30_temp_raw")),
        sht30_humi_raw=_float_or_none(body.get("sht30_humi_raw")),
        bh1750_raw=_int_or_none(body.get("bh1750_raw")),
        accel_x=_int_or_none(body.get("accel_x")),
        accel_y=_int_or_none(body.get("accel_y")),
        accel_z=_int_or_none(body.get("accel_z")),
        gyro_x=_int_or_none(body.get("gyro_x")),
        gyro_y=_int_or_none(body.get("gyro_y")),
        gyro_z=_int_or_none(body.get("gyro_z")),
        mpu_temp_raw=_float_or_none(body.get("mpu_temp_raw")),
        pir_gpio=_int_or_none(body.get("pir_gpio")),
        key_adc=_int_or_none(body.get("key_adc")),
        uart_rx_len=_int_or_none(body.get("uart_rx_len")),
        uart_rx_hex=_str_or_none(body.get("uart_rx_hex")),
        wifi_conn_state=_int_or_none(body.get("wifi_conn_state")),
        wifi_rssi=_int_or_none(body.get("wifi_rssi")),
        wifi_ip=_int_or_none(body.get("wifi_ip")),
        wifi_band=_int_or_none(body.get("wifi_band")),
        wifi_frequency=_int_or_none(body.get("wifi_frequency")),
        lightStatus=_str_or_none(body.get("light_status") or body.get("lightStatus")),
        motorStatus=_str_or_none(body.get("motor_status") or body.get("motorStatus")),
        raw_data=raw_data,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(data)
    db.commit()

    logger.info(
        f"环境数据入库: device={device_id}, temp={data.sht30_temp_raw}, "
        f"humi={data.sht30_humi_raw}, light={data.bh1750_raw}, "
        f"pir={data.pir_gpio}, wifi_conn={data.wifi_conn_state}, "
        f"lightStatus={data.lightStatus}, motorStatus={data.motorStatus}"
    )
    return data
