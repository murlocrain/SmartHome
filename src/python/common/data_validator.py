"""
数据校验器
入库前的字段规则校验、异常数据实时检测、智能字段推荐。
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import func

from common.database import SessionLocal
from common.models import EnvMonitorData
from common.config import logger

# 字段校验规则
VALIDATION_RULES = {
    "sht30_temp_raw": lambda v: -40 <= float(v) <= 125,
    "sht30_humi_raw": lambda v: 0 <= float(v) <= 100,
    "bh1750_raw": lambda v: 0 <= int(v) <= 65535,
    "mq2_adc": lambda v: 0 <= int(v) <= 65535,
    "pir_gpio": lambda v: int(v) in (0, 1),
    "wifi_conn_state": lambda v: int(v) in (0, 1),
    "wifi_rssi": lambda v: -120 <= int(v) <= 0,
    "lightStatus": lambda v: str(v).upper() in ("ON", "OFF"),
    "motorStatus": lambda v: str(v).upper() in ("ON", "OFF"),
    "mpu_temp_raw": lambda v: -40 <= float(v) <= 125,
    "accel_x": lambda v: -32768 <= int(v) <= 32767,
    "accel_y": lambda v: -32768 <= int(v) <= 32767,
    "accel_z": lambda v: -32768 <= int(v) <= 32767,
    "gyro_x": lambda v: -32768 <= int(v) <= 32767,
    "gyro_y": lambda v: -32768 <= int(v) <= 32767,
    "gyro_z": lambda v: -32768 <= int(v) <= 32767,
}


def validate_record(data: dict) -> dict:
    """
    校验单条数据记录。
    返回: { valid: bool, errors: [], warnings: [] }
    """
    errors = []
    warnings = []

    for field, rule in VALIDATION_RULES.items():
        if field not in data or data[field] is None:
            continue
        try:
            if not rule(data[field]):
                errors.append(f"{field}: 值 {data[field]} 超出有效范围")
        except (ValueError, TypeError) as e:
            errors.append(f"{field}: 类型错误 — {e}")

    # 时间戳检查
    ts = data.get("timestamp")
    if ts:
        try:
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if ts > now + timedelta(minutes=5):
                warnings.append("timestamp: 未来时间，可能有时钟偏差")
            if ts < now - timedelta(days=30):
                warnings.append("timestamp: 超过30天前的数据")
        except Exception:
            errors.append("timestamp: 格式无效")

    # 一致性检查
    if "lightStatus" in data and data["lightStatus"] and "wifi_conn_state" in data:
        if data["wifi_conn_state"] == 0 and data.get("lightStatus") == "ON":
            warnings.append("WiFi断开但灯光状态为ON，可能数据不一致")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "field_count": len(data),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def detect_anomalies(device_id: Optional[str] = None, hours: int = 24) -> dict:
    """
    实时异常检测：基于历史窗口的 Z-score / IQR 方法。
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours > 0 else None
        anomalies = []

        fields = ["sht30_temp_raw", "sht30_humi_raw", "bh1750_raw"]
        for field in fields:
            col = getattr(EnvMonitorData, field)
            q = db.query(EnvMonitorData).filter(col.isnot(None))
            if device_id:
                q = q.filter(EnvMonitorData.device_id == device_id)
            if cutoff:
                q = q.filter(EnvMonitorData.timestamp >= cutoff)

            values = [r[0] for r in db.query(col).filter(col.isnot(None)).order_by(col).all()]
            if len(values) < 10:
                continue

            n = len(values)
            p25 = values[n // 4]
            p75 = values[n * 3 // 4]
            iqr = p75 - p25
            lower = p25 - 2.0 * iqr
            upper = p75 + 2.0 * iqr

            # 查询超出上下界的记录
            extreme = db.query(EnvMonitorData).filter(
                col.isnot(None),
                (col < lower) | (col > upper),
            )
            if cutoff:
                extreme = extreme.filter(EnvMonitorData.timestamp >= cutoff)
            if device_id:
                extreme = extreme.filter(EnvMonitorData.device_id == device_id)
            extreme = extreme.order_by(EnvMonitorData.timestamp.desc()).limit(20).all()

            for row in extreme:
                val = getattr(row, field)
                anomalies.append({
                    "id": row.id,
                    "device_id": row.device_id,
                    "field": field,
                    "value": val,
                    "lower_bound": round(lower, 2),
                    "upper_bound": round(upper, 2),
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                })

        return {
            "total_anomalies": len(anomalies),
            "time_range_hours": hours,
            "anomalies": anomalies,
        }
    finally:
        db.close()


def recommend_fields(family_id: int = 1) -> dict:
    """
    智能字段推荐：基于字段完整性历史推荐需要关注的字段。
    """
    db = SessionLocal()
    try:
        q = db.query(EnvMonitorData).filter(EnvMonitorData.family_id == family_id)
        total = q.count()
        if total == 0:
            return {"message": "无历史数据", "recommendations": []}

        schema_fields = [
            "sht30_temp_raw", "sht30_humi_raw", "bh1750_raw",
            "mq2_adc", "pir_gpio", "wifi_rssi", "mpu_temp_raw",
        ]
        recommendations = []

        for field in schema_fields:
            col = getattr(EnvMonitorData, field)
            non_null = q.filter(col.isnot(None)).count()
            ratio = non_null / total
            if ratio < 0.5:
                recommendations.append({
                    "field": field,
                    "completeness": round(ratio, 2),
                    "suggestion": "该字段缺失率较高，建议检查数据源是否正常上报",
                    "severity": "warning" if ratio < 0.2 else "info",
                })

        return {
            "family_id": family_id,
            "total_records": total,
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()
