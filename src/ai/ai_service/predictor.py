"""
ML 预测器 —— 启动时加载模型，提供统一预测接口。
"""
import json
import os
import logging
import numpy as np
import joblib

logger = logging.getLogger(__name__)

_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
)


class Predictor:
    def __init__(self):
        self.reg2 = None   # task2: RandomForestRegressor
        self.clf3 = None   # task3: RandomForestClassifier (多分类)
        self.clf4 = None   # task4: RandomForestClassifier (二分类)
        self.baseline = None
        self._loaded = False

    def load_models(self):
        """启动时调用一次，加载所有模型到内存。"""
        self.reg2 = joblib.load(os.path.join(_MODEL_DIR, "activity_regressor.pkl"))
        self.clf3 = joblib.load(os.path.join(_MODEL_DIR, "scene_predictor.pkl"))
        self.clf4 = joblib.load(os.path.join(_MODEL_DIR, "light_switch_predictor.pkl"))
        with open(os.path.join(_MODEL_DIR, "night_baseline.json"), "r", encoding="utf-8") as f:
            self.baseline = json.load(f)
        self._loaded = True
        logger.info("ML 模型加载完成 (3 模型 + 夜间基线)")

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    # ==================== 任务1: 夜间异常检测 (Z-score 规则) ====================
    def predict_night_anomaly(self, task1_features: dict) -> dict:
        if not self.baseline:
            return {"is_anomalous": False, "zscore": 0.0, "baseline_mean": 0.0, "baseline_std": 0.0, "is_nighttime": False}
        current = task1_features.get("motion_5min_sum", 0)
        mean = self.baseline["global_mean"]
        std = self.baseline["global_std"]
        threshold = self.baseline["z_threshold"]
        z = (current - mean) / (std + 1e-6)
        return {
            "is_anomalous": bool(z > threshold),
            "zscore": round(float(z), 3),
            "current_motion_5min": float(current),
            "threshold": round(mean + threshold * std, 3),
            "baseline_mean": round(mean, 3),
            "baseline_std": round(std, 3),
            "is_nighttime": bool(task1_features.get("is_night", 0)),
        }

    # ==================== 任务2: 活动强度预测 ====================
    def predict_activity(self, task2_features) -> float:
        if self.reg2 is None:
            return 0.0
        # task2_features is a 12-column DataFrame
        val = float(self.reg2.predict(task2_features)[0])
        return round(val, 2)

    # ==================== 任务3: 场景预测 ====================
    def predict_scene(self, task3_features) -> dict:
        if self.clf3 is None:
            return {"scene": "未知", "probability": 0.0, "all_probs": {}, "second": "未知"}
        probs = self.clf3.predict_proba(task3_features)[0]
        idx = int(np.argmax(probs))
        scene = str(self.clf3.classes_[idx])
        prob = round(float(probs[idx]) * 100, 1)
        # 全部概率 & 第二选择
        all_probs = {}
        for i, cls in enumerate(self.clf3.classes_):
            all_probs[str(cls)] = round(float(probs[i]) * 100, 1)
        second_idx = int(np.argsort(probs)[-2])
        second = str(self.clf3.classes_[second_idx])
        return {"scene": scene, "probability": prob, "all_probs": all_probs, "second": second}

    # ==================== 任务4: 灯光开关预测 ====================
    def predict_light(self, task4_features) -> dict:
        if self.clf4 is None:
            return {"will_change": False, "probability": 0.0}
        # 返回正类(1=有变化)的概率
        probs = self.clf4.predict_proba(task4_features)[0]
        pred = int(self.clf4.predict(task4_features)[0])
        # probs 顺序: [class_0, class_1]
        change_prob = round(float(probs[1]) * 100, 1)
        return {"will_change": bool(pred == 1), "probability": change_prob}

    # ==================== 统一预测入口 ====================
    def predict_all(self, features: dict) -> dict:
        """一站式预测。features 来自 feature_engineering.compute_features()。

        Returns 26 字段完整预测结果。
        """
        scene_r = self.predict_scene(features["task3"])
        light_r = self.predict_light(features["task4"])
        night_r = self.predict_night_anomaly(features.get("task1", {}))

        # 特征工程中间值
        df_col = lambda name: float(features.get("_df_latest", {}).get(name, 0))

        result = {
            # 任务1
            "night_anomaly": night_r,
            # 任务2
            "activity": self.predict_activity(features["task2"]),
            "accel_magnitude": df_col("accel_mag"),
            "gyro_magnitude": df_col("gyro_mag"),
            "env_discomfort": df_col("env_discomfort"),
            # 任务3
            "scene": scene_r["scene"],
            "scene_probability": scene_r["probability"],
            "scene_prob_sleep": scene_r["all_probs"].get("睡眠", 0),
            "scene_prob_away": scene_r["all_probs"].get("离家", 0),
            "scene_prob_indoor": scene_r["all_probs"].get("室内活动", 0),
            "scene_prob_other": scene_r["all_probs"].get("其他", 0),
            "scene_second": scene_r["second"],
            # 任务4
            "light_will_change": light_r["will_change"],
            "light_change_probability": light_r["probability"],
            "light_nochange_probability": round(100 - light_r["probability"], 1),
            "light_current_state": bool(df_col("light_status_num")),
            # 通用
            "motion_30min_sum": df_col("motion_30min_sum"),
            "motion_1h_sum": df_col("motion_1h_sum"),
            "no_motion_duration_min": df_col("no_motion_duration_min"),
            "time_since_last_light_change": df_col("time_since_last_light_change"),
        }
        return result


# 全局单例
predictor = Predictor()
