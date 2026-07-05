"""
实时特征工程 —— 从 DB 最近记录计算所有四任务的模型输入特征。
逻辑与 AI数据/特征工程/main1.py 的 create_sleep_features / create_scene_features 一致。
"""
import sys
import os
# 添加 python/ 目录到 sys.path，以便导入 common.* 模块
_python_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'python'))
if _python_dir not in sys.path:
    sys.path.insert(0, _python_dir)

import numpy as np
import pandas as pd

# 抑制新版 pandas FutureWarning（不影响结果）
pd.set_option('future.no_silent_downcasting', True)

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from common.models import EnvMonitorData


def _fetch_recent_data(db: Session, device_id: str, hours: int = 2) -> pd.DataFrame:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    records = (
        db.query(EnvMonitorData)
        .filter(
            EnvMonitorData.device_id == device_id,
            EnvMonitorData.timestamp >= cutoff,
        )
        .order_by(EnvMonitorData.timestamp.asc())
        .all()
    )
    if not records:
        return pd.DataFrame()

    rows = []
    for r in records:
        rows.append({
            "timestamp": pd.Timestamp(r.timestamp),
            "sht30_temp_raw": r.sht30_temp_raw,
            "sht30_humi_raw": r.sht30_humi_raw,
            "bh1750_raw": r.bh1750_raw,
            "pir_gpio": r.pir_gpio,
            "accel_x": r.accel_x,
            "accel_y": r.accel_y,
            "accel_z": r.accel_z,
            "gyro_x": r.gyro_x,
            "gyro_y": r.gyro_y,
            "gyro_z": r.gyro_z,
            "lightStatus": r.lightStatus,
            "motorStatus": r.motorStatus,
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def compute_features(db: Session, device_id: str) -> dict:
    """从 DB 计算当前时刻的四任务特征。

    Returns:
        {
            "task2": pd.DataFrame (1 row, 12 cols),
            "task3": pd.DataFrame (1 row, 24 cols),
            "task4": pd.DataFrame (1 row, 10 cols),
            "task1": dict with keys: is_night, motion_5min_sum, date,
        }
        如果数据不足，返回 None。
    """
    df = _fetch_recent_data(db, device_id, hours=2)
    if df.empty or len(df) < 2:
        return None

    # ==================== 通用时间特征 ====================
    df["hour"] = df["timestamp"].dt.hour
    df["minute_of_day"] = df["hour"] * 60 + df["timestamp"].dt.minute
    df["is_night"] = ((df["hour"] < 6) | (df["hour"] >= 22)).astype(int)
    df["weekday"] = df["timestamp"].dt.weekday
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["date"] = df["timestamp"].dt.date

    # ==================== 加速度/陀螺仪变化 ====================
    for col in ["accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z"]:
        if col in df.columns:
            df[f"{col}_diff"] = df[col].diff().fillna(0)

    accel_diffs = [c for c in ["accel_x_diff", "accel_y_diff", "accel_z_diff"] if c in df.columns]
    gyro_diffs = [c for c in ["gyro_x_diff", "gyro_y_diff", "gyro_z_diff"] if c in df.columns]

    if accel_diffs:
        df["accel_mag"] = np.sqrt(sum(df[c] ** 2 for c in accel_diffs))
    else:
        df["accel_mag"] = 0.0

    if gyro_diffs:
        df["gyro_mag"] = np.sqrt(sum(df[c] ** 2 for c in gyro_diffs))
    else:
        df["gyro_mag"] = 0.0

    # 活动指数 (任务2用 0.5/0.5 权重，任务3用简单求和)
    df["activity_index"] = df["accel_mag"] * 0.5 + df["gyro_mag"] * 0.5

    # ==================== 滚动运动统计 ====================
    df = df.set_index("timestamp")
    df["motion_5min_sum"] = df["pir_gpio"].rolling("5min", min_periods=1).sum()
    df["motion_30min_sum"] = df["pir_gpio"].rolling("30min", min_periods=1).sum()
    df["motion_1h_sum"] = df["pir_gpio"].rolling("1h", min_periods=1).sum()

    # 活动滚动统计 (任务2)
    df["activity_10min_mean"] = df["activity_index"].rolling("10min", min_periods=1).mean()
    df["activity_30min_max"] = df["activity_index"].rolling("30min", min_periods=1).max()

    # 光照滚动统计 (任务4)
    df["light_rolling_mean_10min"] = df["bh1750_raw"].rolling("10min", min_periods=1).mean()
    df["light_rolling_std_10min"] = df["bh1750_raw"].rolling("10min", min_periods=1).std()
    df["light_rolling_std_10min"] = df["light_rolling_std_10min"].fillna(0)

    df = df.reset_index()

    # ==================== 环境舒适度 (任务2) ====================
    df["temp_comfort"] = ((df["sht30_temp_raw"] >= 22) & (df["sht30_temp_raw"] <= 28)).astype(int)
    df["humi_comfort"] = ((df["sht30_humi_raw"] >= 40) & (df["sht30_humi_raw"] <= 60)).astype(int)
    df["env_discomfort"] = np.sqrt(
        ((df["sht30_temp_raw"] - 25) ** 2 / 9) + ((df["sht30_humi_raw"] - 50) ** 2 / 100)
    )

    # ==================== 连续无人时长 ====================
    df["no_motion_group"] = (df["pir_gpio"] == 0).astype(int)
    df["group_change"] = df["no_motion_group"].diff().fillna(0).ne(0).cumsum()
    no_motion_mask = df["pir_gpio"] == 0
    durations = df[no_motion_mask].groupby("group_change")["timestamp"].transform(
        lambda x: (x.max() - x.min()).total_seconds() / 60
    )
    df["no_motion_duration_min"] = np.nan
    df.loc[no_motion_mask, "no_motion_duration_min"] = durations
    df["no_motion_duration_min"] = df["no_motion_duration_min"].fillna(0)

    # ==================== 分桶特征 (任务3) ====================
    light_bins = [-1, 10, 100, 1000, np.inf]
    light_labels = ["暗", "中", "亮", "极亮"]
    df["light_level"] = pd.cut(df["bh1750_raw"], bins=light_bins, labels=light_labels)

    df["temp_level"] = pd.cut(
        df["sht30_temp_raw"], bins=[-10, 15, 25, 30, 50], labels=["冷", "凉爽", "温暖", "热"]
    )
    df["humi_level"] = pd.cut(
        df["sht30_humi_raw"], bins=[0, 30, 60, 100], labels=["干燥", "舒适", "潮湿"]
    )
    df["activity_level"] = pd.qcut(
        df["activity_index"], q=3, labels=["低", "中", "高"], duplicates="drop"
    )

    # ==================== 场景规则标签 ====================
    def assign_scene(row):
        if row["is_night"] and row["pir_gpio"] == 0 and row["light_level"] == "暗":
            return "睡眠"
        if row["pir_gpio"] == 0 and row["motion_30min_sum"] == 0:
            return "离家"
        if row["pir_gpio"] == 1:
            return "室内活动"
        return "其他"

    df["scene"] = df.apply(assign_scene, axis=1)

    # ==================== 灯光相关 (任务4) ====================
    df["lightStatus"] = df["lightStatus"].fillna("OFF").str.upper()
    df["light_status_num"] = df["lightStatus"].map({"ON": 1, "OFF": 0}).fillna(0)
    df["light_changed"] = df["light_status_num"].diff().fillna(0).ne(0).astype(int)

    # 距上次灯光变化时间
    change_times = df.loc[df["light_changed"] == 1, "timestamp"]
    df["time_since_last_light_change"] = np.nan
    for i, row in df.iterrows():
        past = change_times[change_times < row["timestamp"]]
        if not past.empty:
            df.at[i, "time_since_last_light_change"] = (row["timestamp"] - past.max()).total_seconds()
        else:
            df.at[i, "time_since_last_light_change"] = 999999

    df["temp_current"] = df["sht30_temp_raw"]
    df["humi_current"] = df["sht30_humi_raw"]
    df["motor_status_num"] = df["motorStatus"].fillna("OFF").str.upper().map({"ON": 1, "OFF": 0}).fillna(0)

    # ==================== 提取最后一行特征 ====================
    latest = df.iloc[-1]

    # --- 任务1 ---
    task1 = {
        "is_night": int(latest["is_night"]),
        "motion_5min_sum": float(latest["motion_5min_sum"]),
        "date": str(latest["date"]),
    }

    # --- 任务2 (12列) ---
    feats2 = [
        "hour", "minute_of_day", "is_night", "pir_gpio", "motion_5min_sum",
        "motion_30min_sum", "activity_index", "activity_10min_mean",
        "activity_30min_max", "temp_comfort", "humi_comfort", "env_discomfort",
    ]
    task2 = pd.DataFrame([latest[feats2].fillna(0).values], columns=feats2)

    # --- 任务3 (24列，必须与 task3_feature_names.json 对齐) ---
    cat_features = {
        "light_level": {"col": "light", "cats": ["暗", "中", "亮", "极亮"]},
        "temp_level": {"col": "temp", "cats": ["冷", "凉爽", "温暖", "热"]},
        "humi_level": {"col": "humi", "cats": ["干燥", "舒适", "潮湿"]},
        "activity_level": {"col": "act", "cats": ["低", "中", "高"]},
        "scene": {"col": "current_scene", "cats": ["睡眠", "离家", "室内活动", "其他"]},
    }

    dummy_parts = {}
    for feat, info in cat_features.items():
        val = latest.get(feat, None)
        for cat in info["cats"]:
            col_name = f'{info["col"]}_{cat}'
            dummy_parts[col_name] = 1 if val == cat else 0

    num_feats3_raw = {
        "hour": latest["hour"],
        "minute_of_day": latest["minute_of_day"],
        "is_night": latest["is_night"],
        "weekday": latest["weekday"],
        "is_weekend": latest["is_weekend"],
        "motion_30min_sum": latest["motion_30min_sum"],
        "motion_1h_sum": latest["motion_1h_sum"],
        "activity_index": latest["activity_index"],
        "no_motion_duration_min": latest["no_motion_duration_min"],
    }

    import json
    feat_names_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "models", "task3_feature_names.json",
    )
    with open(feat_names_path, "r", encoding="utf-8") as f:
        ordered_names = json.load(f)

    feat3_dict = {}
    feat3_dict.update({k: num_feats3_raw.get(k, 0) for k in ordered_names if k in num_feats3_raw})
    feat3_dict.update({k: dummy_parts.get(k, 0) for k in ordered_names if k in dummy_parts})
    feat3_row = [feat3_dict.get(k, 0) for k in ordered_names]
    task3 = pd.DataFrame([feat3_row], columns=ordered_names)

    # --- 任务4 (10列) ---
    feats4 = [
        "hour", "minute_of_day", "is_night", "pir_gpio",
        "light_rolling_mean_10min", "light_rolling_std_10min",
        "time_since_last_light_change", "temp_current", "humi_current",
        "motor_status_num",
    ]
    task4 = pd.DataFrame([latest[feats4].fillna(0).values], columns=feats4)

    return {"task1": task1, "task2": task2, "task3": task3, "task4": task4, "_df_latest": {
        "accel_mag": float(latest.get("accel_mag", 0)),
        "gyro_mag": float(latest.get("gyro_mag", 0)),
        "env_discomfort": float(latest.get("env_discomfort", 0)),
        "light_status_num": int(latest.get("light_status_num", 0)),
        "motion_30min_sum": float(latest.get("motion_30min_sum", 0)),
        "motion_1h_sum": float(latest.get("motion_1h_sum", 0)),
        "no_motion_duration_min": float(latest.get("no_motion_duration_min", 0)),
        "time_since_last_light_change": float(latest.get("time_since_last_light_change", 0)),
    }}
