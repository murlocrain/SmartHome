-- 智能家居IoT平台 - MySQL数据库初始化脚本

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS smart_home CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_home;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    privacy_settings JSON DEFAULT '{"personalization": true, "data_collection": true}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 家庭表
CREATE TABLE IF NOT EXISTS families (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 家庭成员表
CREATE TABLE IF NOT EXISTS family_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    user_id INT NOT NULL,
    role VARCHAR(32) DEFAULT 'member' NOT NULL,
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(family_id, user_id),
    FOREIGN KEY (family_id) REFERENCES families(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 房间表
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    family_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 设备表
CREATE TABLE IF NOT EXISTS devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(64) UNIQUE NOT NULL,
    device_type VARCHAR(32) NOT NULL,
    name VARCHAR(100),
    family_id INT NOT NULL,
    room_id INT,
    capabilities JSON,
    config JSON,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_devices_family_id ON devices(family_id);
CREATE INDEX idx_devices_device_id ON devices(device_id);


-- 设备分组表
CREATE TABLE IF NOT EXISTS device_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    family_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_device_groups_family_id ON device_groups(family_id);


-- 设备分组成员表
CREATE TABLE IF NOT EXISTS device_group_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    device_id INT NOT NULL,
    UNIQUE(group_id, device_id),
    FOREIGN KEY (group_id) REFERENCES device_groups(id),
    FOREIGN KEY (device_id) REFERENCES devices(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 环境监控数据表 (时序数据)
-- 对齐 ORM 模型 common.models.EnvMonitorData / APP.models.EnvMonitorData
CREATE TABLE IF NOT EXISTS env_monitor_data (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL,
    family_id INT NOT NULL,
    room_id INT,
    mq2_adc INT,
    sht30_temp_raw FLOAT,
    sht30_humi_raw FLOAT,
    bh1750_raw INT,
    accel_x INT,
    accel_y INT,
    accel_z INT,
    gyro_x INT,
    gyro_y INT,
    gyro_z INT,
    mpu_temp_raw FLOAT,
    pir_gpio INT,
    key_adc INT,
    uart_rx_len INT,
    uart_rx_hex VARCHAR(50),
    wifi_conn_state INT,
    wifi_rssi INT,
    wifi_ip INT,
    wifi_band INT,
    wifi_frequency INT,
    lightStatus VARCHAR(10),
    motorStatus VARCHAR(10),
    raw_data JSON,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_env_monitor_data_family_id ON env_monitor_data(family_id);
CREATE INDEX idx_env_monitor_data_device_id ON env_monitor_data(device_id);
CREATE INDEX idx_env_monitor_data_timestamp ON env_monitor_data(`timestamp`);


-- AI 预测结果表
-- 对齐 ORM 模型 common.models.AIPrediction
CREATE TABLE IF NOT EXISTS ai_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    is_night_anomalous BOOLEAN DEFAULT FALSE,
    night_zscore FLOAT DEFAULT 0.0,
    night_current_motion FLOAT DEFAULT 0.0,
    night_baseline_mean FLOAT DEFAULT 0.0,
    night_baseline_std FLOAT DEFAULT 0.0,
    night_is_nighttime BOOLEAN DEFAULT FALSE,
    activity_index FLOAT DEFAULT 0.0,
    accel_magnitude FLOAT DEFAULT 0.0,
    gyro_magnitude FLOAT DEFAULT 0.0,
    env_discomfort FLOAT DEFAULT 0.0,
    scene VARCHAR(20),
    scene_probability FLOAT DEFAULT 0.0,
    scene_prob_sleep FLOAT DEFAULT 0.0,
    scene_prob_away FLOAT DEFAULT 0.0,
    scene_prob_indoor FLOAT DEFAULT 0.0,
    scene_prob_other FLOAT DEFAULT 0.0,
    scene_second VARCHAR(20),
    light_will_change BOOLEAN DEFAULT FALSE,
    light_change_probability FLOAT DEFAULT 0.0,
    light_nochange_probability FLOAT DEFAULT 0.0,
    light_current_state BOOLEAN DEFAULT FALSE,
    motion_30min_sum FLOAT DEFAULT 0.0,
    motion_1h_sum FLOAT DEFAULT 0.0,
    no_motion_duration_min FLOAT DEFAULT 0.0,
    time_since_last_light_change FLOAT DEFAULT 0.0,
    predict_time DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_ai_predictions_device_id ON ai_predictions(device_id);
CREATE INDEX idx_ai_predictions_predict_time ON ai_predictions(predict_time);


-- 场景规则表
CREATE TABLE IF NOT EXISTS scene_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    scene_id VARCHAR(64) UNIQUE NOT NULL,
    conditions JSON NOT NULL,
    actions JSON NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_scene_rules_family_id ON scene_rules(family_id);


-- 场景事件日志表
CREATE TABLE IF NOT EXISTS scene_event_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    family_id INT NOT NULL,
    rule_id INT,
    scene_id VARCHAR(64),
    event_type VARCHAR(64) NOT NULL,
    description VARCHAR(500),
    suggestion VARCHAR(500),
    details JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (family_id) REFERENCES families(id),
    FOREIGN KEY (rule_id) REFERENCES scene_rules(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_scene_event_logs_family_id ON scene_event_logs(family_id);


-- 网关连接日志表
CREATE TABLE IF NOT EXISTS gateway_connection_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    family_id VARCHAR(64) NOT NULL,
    connection_type VARCHAR(32) NOT NULL,
    client_id VARCHAR(128),
    status VARCHAR(32) NOT NULL,
    ip_address VARCHAR(50),
    details JSON,
    connected_at DATETIME,
    disconnected_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_gateway_connection_logs_family_id ON gateway_connection_logs(family_id);


-- 网关MQTT消息日志表
CREATE TABLE IF NOT EXISTS gateway_mqtt_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    family_id VARCHAR(64),
    device_id VARCHAR(64),
    topic VARCHAR(255) NOT NULL,
    payload JSON,
    message_type VARCHAR(32),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_gateway_mqtt_logs_family_id ON gateway_mqtt_logs(family_id);
CREATE INDEX idx_gateway_mqtt_logs_device_id ON gateway_mqtt_logs(device_id);

-- 插入默认数据
INSERT INTO users (username, email, phone, hashed_password) 
SELECT 'admin', 'admin@example.com', '13800138000', 'hashed_password_placeholder'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin');

INSERT INTO families (name, owner_id)
SELECT '默认家庭', (SELECT id FROM users WHERE username = 'admin')
WHERE NOT EXISTS (SELECT 1 FROM families WHERE name = '默认家庭');

INSERT INTO rooms (name, family_id)
SELECT '客厅', (SELECT id FROM families WHERE name = '默认家庭')
WHERE NOT EXISTS (SELECT 1 FROM rooms WHERE name = '客厅');

SELECT '数据库初始化完成' AS result;
