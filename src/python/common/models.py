from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20), unique=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    privacy_settings = Column(JSON, default=lambda: {"personalization": True, "data_collection": True})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Family(Base):
    __tablename__ = "families"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class FamilyMember(Base):
    __tablename__ = "family_members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    role = Column(String(32), default="member")
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    family_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), unique=True, nullable=False)
    device_type = Column(String(32), nullable=False)
    name = Column(String(100))
    family_id = Column(Integer, nullable=False)
    room_id = Column(Integer)
    capabilities = Column(JSON)
    config = Column(JSON)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DeviceGroup(Base):
    __tablename__ = "device_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    family_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DeviceGroupMember(Base):
    __tablename__ = "device_group_members"
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, nullable=False)
    device_id = Column(Integer, nullable=False)


class EnvMonitorData(Base):
    """环境监测数据 —— 对齐设备上报的 22 个字段。
    body_state / wifi_state 为派生字段不存库，查询时按 pir_gpio / wifi_conn_state 推导。
    """
    __tablename__ = "env_monitor_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), nullable=False)
    family_id = Column(Integer, nullable=False)
    room_id = Column(Integer, nullable=True)
    # --- 传感器 ---
    mq2_adc = Column(Integer)
    sht30_temp_raw = Column(Float)
    sht30_humi_raw = Column(Float)
    bh1750_raw = Column(Integer)
    accel_x = Column(Integer)
    accel_y = Column(Integer)
    accel_z = Column(Integer)
    gyro_x = Column(Integer)
    gyro_y = Column(Integer)
    gyro_z = Column(Integer)
    mpu_temp_raw = Column(Float)
    pir_gpio = Column(Integer)
    key_adc = Column(Integer)
    uart_rx_len = Column(Integer)
    uart_rx_hex = Column(String(50))
    wifi_conn_state = Column(Integer)
    wifi_rssi = Column(Integer)
    wifi_ip = Column(Integer)
    wifi_band = Column(Integer)
    wifi_frequency = Column(Integer)
    lightStatus = Column(String(10))
    motorStatus = Column(String(10))
    raw_data = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AIPrediction(Base):
    """AI 模型预测结果，每次收到传感器数据后写入一条。"""
    __tablename__ = "ai_predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, nullable=False)
    device_id = Column(String(64), nullable=False)
    # ── 任务1: 夜间异常 ──
    is_night_anomalous = Column(Boolean, default=False)
    night_zscore = Column(Float, default=0.0)
    night_current_motion = Column(Float, default=0.0)
    night_baseline_mean = Column(Float, default=0.0)
    night_baseline_std = Column(Float, default=0.0)
    night_is_nighttime = Column(Boolean, default=False)
    # ── 任务2: 活动强度 ──
    activity_index = Column(Float, default=0.0)
    accel_magnitude = Column(Float, default=0.0)
    gyro_magnitude = Column(Float, default=0.0)
    env_discomfort = Column(Float, default=0.0)
    # ── 任务3: 场景识别 ──
    scene = Column(String(20))
    scene_probability = Column(Float, default=0.0)
    scene_prob_sleep = Column(Float, default=0.0)
    scene_prob_away = Column(Float, default=0.0)
    scene_prob_indoor = Column(Float, default=0.0)
    scene_prob_other = Column(Float, default=0.0)
    scene_second = Column(String(20))
    # ── 任务4: 灯光开关 ──
    light_will_change = Column(Boolean, default=False)
    light_change_probability = Column(Float, default=0.0)
    light_nochange_probability = Column(Float, default=0.0)
    light_current_state = Column(Boolean, default=False)
    # ── 通用特征 ──
    motion_30min_sum = Column(Float, default=0.0)
    motion_1h_sum = Column(Float, default=0.0)
    no_motion_duration_min = Column(Float, default=0.0)
    time_since_last_light_change = Column(Float, default=0.0)
    predict_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SceneRule(Base):
    __tablename__ = "scene_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)
    scene_id = Column(String(64), unique=True, nullable=False)
    conditions = Column(JSON, nullable=False)
    actions = Column(JSON, nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SceneEventLog(Base):
    __tablename__ = "scene_event_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(Integer, nullable=False)
    rule_id = Column(Integer)
    scene_id = Column(String(64))
    event_type = Column(String(64), nullable=False)
    description = Column(String(500))
    suggestion = Column(String(500))
    details = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GatewayConnectionLog(Base):
    __tablename__ = "gateway_connection_logs"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    family_id = Column(String(64), nullable=False)
    connection_type = Column(String(32), nullable=False)
    client_id = Column(String(128))
    status = Column(String(32), nullable=False)
    ip_address = Column(String(50))
    details = Column(JSON)
    connected_at = Column(DateTime)
    disconnected_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
