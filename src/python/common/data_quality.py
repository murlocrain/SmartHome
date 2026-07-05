"""
数据质量分析器
对 EnvMonitorData 表的字段完整性、准确性、一致性进行系统性分析。
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import func, and_

from common.database import SessionLocal
from common.models import EnvMonitorData
from common.config import logger

# 各字段有效取值范围
FIELD_RANGE = {
    "mq2_adc": (0, 65535),
    "sht30_temp_raw": (-40.0, 125.0),
    "sht30_humi_raw": (0.0, 100.0),
    "bh1750_raw": (0, 65535),
    "accel_x": (-32768, 32767),
    "accel_y": (-32768, 32767),
    "accel_z": (-32768, 32767),
    "gyro_x": (-32768, 32767),
    "gyro_y": (-32768, 32767),
    "gyro_z": (-32768, 32767),
    "mpu_temp_raw": (-40.0, 125.0),
    "pir_gpio": (0, 1),
    "key_adc": (0, 65535),
    "uart_rx_len": (0, 65535),
    "wifi_conn_state": (0, 1),
    "wifi_rssi": (-120, 0),
    "wifi_band": (0, 5),
    "lightStatus": ("ON", "OFF"),
    "motorStatus": ("ON", "OFF"),
}


def quality_report(device_id: Optional[str] = None, hours: int = 24) -> dict:
    """生成数据质量报告"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

        q = db.query(EnvMonitorData)
        if device_id:
            q = q.filter(EnvMonitorData.device_id == device_id)
        if hours > 0:
            q = q.filter(EnvMonitorData.timestamp >= cutoff)

        total = q.count()
        if total == 0:
            return {"total_records": 0, "message": "指定范围内无数据"}

        # ========== 字段完整性 ==========
        completeness = {}
        accuracy = {}
        field_stats = {}
        schema_fields = [
            "mq2_adc", "sht30_temp_raw", "sht30_humi_raw", "bh1750_raw",
            "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z",
            "mpu_temp_raw", "pir_gpio", "key_adc",
            "uart_rx_len", "uart_rx_hex",
            "wifi_conn_state", "wifi_rssi", "wifi_ip", "wifi_band", "wifi_frequency",
            "lightStatus", "motorStatus",
        ]

        for field in schema_fields:
            col = getattr(EnvMonitorData, field, None)
            if col is None:
                continue

            non_null = q.filter(col.isnot(None)).count()
            null_count = total - non_null
            completeness[field] = {
                "non_null": non_null,
                "null": null_count,
                "completeness_ratio": round(non_null / total, 4) if total > 0 else 0,
            }

            # 数值字段：准确性和统计
            field_range = FIELD_RANGE.get(field)
            if field_range and isinstance(field_range[0], (int, float)):
                stats = db.query(
                    func.min(col).label("min"),
                    func.max(col).label("max"),
                    func.avg(col).label("avg"),
                ).filter(
                    col.isnot(None),
                    EnvMonitorData.timestamp >= cutoff if hours > 0 else True,
                ).first()

                out_of_range = 0
                if stats and stats.min is not None:
                    out_of_range = q.filter(
                        col.isnot(None),
                        (col < field_range[0]) | (col > field_range[1]),
                    ).count()

                accuracy[field] = {
                    "valid_range": list(field_range),
                    "out_of_range_count": out_of_range,
                    "out_of_range_ratio": round(out_of_range / total, 4) if total > 0 else 0,
                }

                if stats:
                    field_stats[field] = {
                        "min": round(stats.min, 2) if stats.min else None,
                        "max": round(stats.max, 2) if stats.max else None,
                        "avg": round(stats.avg, 2) if stats.avg else None,
                    }

        # ========== 一致性：时间戳顺序 ==========
        records = q.order_by(EnvMonitorData.timestamp.asc()).all()
        time_gaps = 0
        out_of_order = 0
        if len(records) >= 2:
            prev = records[0].timestamp
            for r in records[1:]:
                if r.timestamp and prev:
                    diff = (r.timestamp - prev).total_seconds()
                    if diff < 0:
                        out_of_order += 1
                    elif diff > 300:  # gap > 5 min
                        time_gaps += 1
                if r.timestamp:
                    prev = r.timestamp

        consistency = {
            "total_records": total,
            "out_of_order_timestamps": out_of_order,
            "large_time_gaps": time_gaps,
        }

        # ========== 综合评分 ==========
        avg_completeness = (
            sum(v["completeness_ratio"] for v in completeness.values()) / len(completeness)
            if completeness else 1
        )
        avg_accuracy = (
            sum((1 - max(v.get("out_of_range_ratio", 0), 0) for v in accuracy.values()))
            / len(accuracy) if accuracy else 1
        )
        quality_score = round((avg_completeness * 0.5 + avg_accuracy * 0.5) * 100, 1)

        return {
            "total_records": total,
            "time_range_hours": hours,
            "device_id": device_id,
            "completeness": completeness,
            "accuracy": accuracy,
            "consistency": consistency,
            "field_statistics": field_stats,
            "quality_score": quality_score,
            "grade": (
                "优秀" if quality_score >= 95 else
                "良好" if quality_score >= 85 else
                "一般" if quality_score >= 70 else
                "较差"
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    finally:
        db.close()
