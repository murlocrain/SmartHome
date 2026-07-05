"""
数据统计分析器
字段分布统计、异常值检测、关联性分析、趋势分析。
"""
import math
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import func

from common.database import SessionLocal
from common.models import EnvMonitorData
from common.config import logger


def distribution(device_id: Optional[str] = None, hours: int = 24) -> dict:
    """数值字段分布统计（min/max/mean/median/std/percentiles）"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours > 0 else None
        q = db.query(EnvMonitorData)
        if device_id:
            q = q.filter(EnvMonitorData.device_id == device_id)
        if cutoff:
            q = q.filter(EnvMonitorData.timestamp >= cutoff)

        total = q.count()
        if total == 0:
            return {"total": 0, "message": "无数据"}

        fields = ["sht30_temp_raw", "sht30_humi_raw", "bh1750_raw", "mpu_temp_raw", "wifi_rssi"]
        result = {}

        for field in fields:
            col = getattr(EnvMonitorData, field)
            stats = db.query(
                func.min(col), func.max(col), func.avg(col),
                func.count(col),
            ).filter(col.isnot(None), *([EnvMonitorData.timestamp >= cutoff] if cutoff else [])).first()

            if not stats or stats[0] is None:
                continue

            values = [
                r[0] for r in db.query(col).filter(col.isnot(None), *([EnvMonitorData.timestamp >= cutoff] if cutoff else [])).order_by(col).all()
            ]

            if not values:
                continue

            n = len(values)
            # 中位数和分位数
            median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2
            p25 = values[max(0, n // 4)]
            p75 = values[min(n - 1, n * 3 // 4)]

            # 标准差
            avg = stats[2]
            variance = sum((v - avg) ** 2 for v in values) / n
            std = math.sqrt(variance) if variance > 0 else 0

            # 异常值检测 (IQR)
            iqr = (p75 - p25) if p75 is not None and p25 is not None else 0
            lower = p25 - 1.5 * iqr if iqr else None
            upper = p75 + 1.5 * iqr if iqr else None
            outliers = sum(1 for v in values if (lower is not None and v < lower) or (upper is not None and v > upper))

            result[field] = {
                "count": n,
                "min": round(stats[0], 2),
                "max": round(stats[1], 2),
                "mean": round(avg, 2),
                "median": round(median, 2),
                "std": round(std, 2),
                "p25": round(p25, 2),
                "p75": round(p75, 2),
                "iqr": round(iqr, 2),
                "outlier_count": outliers,
                "outlier_ratio": round(outliers / n, 4) if n > 0 else 0,
            }

        result["total_records"] = total
        result["time_range_hours"] = hours
        return result
    finally:
        db.close()


def correlation(device_id: Optional[str] = None, hours: int = 24) -> dict:
    """Pearson 相关系数矩阵（温度/湿度/光照之间）"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours > 0 else None
        q = db.query(EnvMonitorData)
        if device_id:
            q = q.filter(EnvMonitorData.device_id == device_id)
        if cutoff:
            q = q.filter(EnvMonitorData.timestamp >= cutoff)

        rows = q.filter(
            EnvMonitorData.sht30_temp_raw.isnot(None),
            EnvMonitorData.sht30_humi_raw.isnot(None),
            EnvMonitorData.bh1750_raw.isnot(None),
        ).all()

        if len(rows) < 3:
            return {"message": "数据量不足，至少需要3条", "count": len(rows)}

        temps = [r.sht30_temp_raw for r in rows]
        humis = [r.sht30_humi_raw for r in rows]
        lights = [float(r.bh1750_raw) for r in rows]

        def pearson(x, y):
            n = len(x)
            if n < 2:
                return 0
            mean_x = sum(x) / n
            mean_y = sum(y) / n
            cov = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
            std_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
            std_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
            if std_x == 0 or std_y == 0:
                return 0
            return cov / (std_x * std_y)

        return {
            "count": len(rows),
            "temp_humi_corr": round(pearson(temps, humis), 4),
            "temp_light_corr": round(pearson(temps, lights), 4),
            "humi_light_corr": round(pearson(humis, lights), 4),
        }
    finally:
        db.close()


def trends(device_id: Optional[str] = None, field: str = "sht30_temp_raw", hours: int = 24, interval: str = "hour") -> dict:
    """时间序列趋势分析：按 interval 聚合 field 的均值/计数"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours > 0 else None
        col = getattr(EnvMonitorData, field, None)
        if col is None:
            return {"error": f"未知字段: {field}"}

        # MySQL 聚合
        time_trunc = {
            "hour": func.date_format(EnvMonitorData.timestamp, "%Y-%m-%d %H:00"),
            "minute": func.date_format(EnvMonitorData.timestamp, "%Y-%m-%d %H:%i"),
            "day": func.date_format(EnvMonitorData.timestamp, "%Y-%m-%d"),
        }.get(interval, func.date_format(EnvMonitorData.timestamp, "%Y-%m-%d %H:00"))

        q = db.query(
            time_trunc.label("bucket"),
            func.avg(col).label("avg_val"),
            func.min(col).label("min_val"),
            func.max(col).label("max_val"),
            func.count(col).label("cnt"),
        ).filter(col.isnot(None))

        if device_id:
            q = q.filter(EnvMonitorData.device_id == device_id)
        if cutoff:
            q = q.filter(EnvMonitorData.timestamp >= cutoff)

        q = q.group_by("bucket").order_by("bucket").limit(200)

        points = []
        for row in q.all():
            points.append({
                "time": row[0],
                "avg": round(row[1], 2) if row[1] else None,
                "min": round(row[2], 2) if row[2] else None,
                "max": round(row[3], 2) if row[3] else None,
                "count": row[4],
            })

        return {
            "field": field,
            "interval": interval,
            "hours": hours,
            "points_count": len(points),
            "points": points,
        }
    finally:
        db.close()


def frequency_report(device_id: Optional[str] = None, hours: int = 24) -> dict:
    """分类字段频次统计"""
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours) if hours > 0 else None
        q = db.query(EnvMonitorData)
        if device_id:
            q = q.filter(EnvMonitorData.device_id == device_id)
        if cutoff:
            q = q.filter(EnvMonitorData.timestamp >= cutoff)

        result = {}
        for field in ["lightStatus", "motorStatus", "pir_gpio", "wifi_conn_state"]:
            col = getattr(EnvMonitorData, field)
            counts = db.query(col, func.count()).filter(col.isnot(None)).group_by(col).all()
            result[field] = {str(k): v for k, v in counts}

        return result
    finally:
        db.close()
