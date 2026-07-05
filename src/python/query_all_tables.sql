-- 查询所有表的SQL文件 (PostgreSQL)
-- 生成时间: 2026-06-11

-- 1. 用户相关表 (user_service)

-- 用户表
SELECT * FROM users;

-- 家庭表
SELECT * FROM families;

-- 家庭成员表
SELECT * FROM family_members;

-- 房间表
SELECT * FROM rooms;


-- 2. 设备相关表 (device_service)

-- 设备表
SELECT * FROM devices;

-- 设备分组表
SELECT * FROM device_groups;

-- 设备分组成员表
SELECT * FROM device_group_members;

-- 环境监测数据表
SELECT * FROM env_monitor_data;


-- 3. 网关相关表 (gateway_service)

-- 网关连接日志表
SELECT * FROM gateway_connection_logs;

-- MQTT消息日志表
SELECT * FROM mqtt_message_logs;


-- 4. 场景相关表 (scene_service)

-- 场景规则表
SELECT * FROM scene_rules;

-- 场景事件日志表
SELECT * FROM scene_event_logs;
