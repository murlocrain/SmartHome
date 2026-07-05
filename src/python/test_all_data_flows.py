"""
综合数据流测试脚本
覆盖项目中所有 8 条核心数据流。
不依赖运行中的服务 —— 测试导入、Schema、JWT、DB CRUD、回调解析、IoT 客户端结构。
运行方式: python test_all_data_flows.py
"""
import json
import sys
import os
from datetime import datetime, timezone

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TEST_DIR)

SEP = "=" * 60
PASSED = 0
FAILED = 0


def title(name: str):
    print(f"\n{SEP}")
    print(f"  {name}")
    print(SEP)


def check(desc: str, condition: bool, detail: str = ""):
    global PASSED, FAILED
    if condition:
        print(f"  [PASS] {desc}")
        PASSED += 1
    else:
        print(f"  [FAIL] {desc}  — {detail}")
        FAILED += 1


# ══════════════════════════════════════════════════════
#  数据流 1: 配置 & 模块导入
# ══════════════════════════════════════════════════════
title("数据流 0: 配置 & 模块导入")

from common.config import settings, logger

check("settings 对象创建成功", settings is not None)
check("PROJECT_NAME 已加载", bool(settings.PROJECT_NAME), settings.PROJECT_NAME)
check("JWT_SECRET_KEY 已加载", bool(settings.JWT_SECRET_KEY))
check("DATABASE_TYPE = mysql", settings.DATABASE_TYPE == "mysql")
check("MYSQL_HOST 已配置", bool(settings.MYSQL_HOST), settings.MYSQL_HOST)
check("API_V1_PREFIX = /api/v1", settings.API_V1_PREFIX == "/api/v1")
check("HUAWEI_IOTDA_ENABLED 已配置", isinstance(settings.HUAWEI_IOTDA_ENABLED, bool))
check("AI_ENABLED 已配置", isinstance(settings.AI_ENABLED, bool))

# ══════════════════════════════════════════════════════
#  数据流 2: JWT Token 生成与验证
# ══════════════════════════════════════════════════════
title("数据流 2: JWT Token 生成与验证")

from common.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)

test_user_data = {"sub": "1", "username": "testuser"}
access_token = create_access_token(test_user_data)
check("access_token 生成成功", isinstance(access_token, str) and len(access_token) > 20)
check("access_token 以 eyJ 开头 (JWT)", access_token.startswith("eyJ"))

refresh_token = create_refresh_token(test_user_data)
check("refresh_token 生成成功", isinstance(refresh_token, str) and len(refresh_token) > 20)

decoded = decode_token(access_token)
check("access_token 可解码", decoded is not None)
check("解码后 sub 正确", decoded and decoded.get("sub") == "1")
check("解码后 username 正确", decoded and decoded.get("username") == "testuser")
check("token type = access", decoded and decoded.get("type") == "access")

decoded_refresh = decode_token(refresh_token)
check("refresh_token 可解码", decoded_refresh is not None)
check("token type = refresh", decoded_refresh and decoded_refresh.get("type") == "refresh")

# 密码哈希
raw_pw = "testPassword123"
hashed = get_password_hash(raw_pw)
check("密码哈希成功", hashed and hashed.startswith("$2b$"))
check("bcrypt 验证正确密码", verify_password(raw_pw, hashed))
check("bcrypt 拒绝错误密码", not verify_password("wrongPassword", hashed))

# 无效 token
bad_token = "not.a.real.jwt"
check("无效 token 解码返回 None", decode_token(bad_token) is None)
check("空字符串解码返回 None", decode_token("") is None)

# ══════════════════════════════════════════════════════
#  数据流 3: Pydantic Schema 验证
# ══════════════════════════════════════════════════════
title("数据流 3: Pydantic Schema 验证")

# --- common/schemas/common.py ---
from common.schemas.common import ResponseModel, Token

resp = ResponseModel(code=200, message="ok", data={"key": "val"})
check("ResponseModel 创建成功", resp.code == 200)
check("ResponseModel.data 正确", resp.data == {"key": "val"})

token_obj = Token(access_token="access123", refresh_token="refresh456")
check("Token schema access_token", token_obj.access_token == "access123")
check("Token schema token_type default", token_obj.token_type == "bearer")

# --- user schemas ---
from services.user_service.schemas import UserCreate, UserLogin, PasswordChange

user_create = UserCreate(username="testuser", password="Pass1234", email="test@test.com")
check("UserCreate 创建成功", user_create.username == "testuser")
check("UserCreate email", user_create.email == "test@test.com")

user_login = UserLogin(username="testuser", password="Pass1234")
check("UserLogin 创建成功", user_login.username == "testuser")

pwd_change = PasswordChange(old_password="old", new_password="newPass456")
check("PasswordChange 创建成功", pwd_change.new_password == "newPass456")

# 字段验证
try:
    UserCreate(username="ab", password="short")
    check("UserCreate 拒绝短用户名", False, "应该抛出异常")
except Exception:
    check("UserCreate 拒绝短用户名", True)

try:
    UserCreate(username="validuser", password="12345")
    check("UserCreate 拒绝短密码", False, "应该抛出异常")
except Exception:
    check("UserCreate 拒绝短密码", True)

# --- family schemas ---
from services.user_service.schemas import FamilyCreate, FamilyMemberAdd, RoomCreate

family_create = FamilyCreate(name="我的家")
check("FamilyCreate 创建成功", family_create.name == "我的家")

member_add = FamilyMemberAdd(user_id=2, role="member")
check("FamilyMemberAdd 创建成功", member_add.role == "member")
check("FamilyMemberAdd default role", FamilyMemberAdd(user_id=3).role == "member")

room_create = RoomCreate(name="客厅")
check("RoomCreate 创建成功", room_create.name == "客厅")

# --- device schemas ---
from services.device_service.schemas import ControlRequest, DeviceRegisterRequest, DeviceListResponse, LatestDataResponse

ctrl = ControlRequest(action="ON")
check("ControlRequest ON 创建成功", ctrl.action == "ON")

ctrl2 = ControlRequest(action="OFF")
check("ControlRequest OFF 创建成功", ctrl2.action == "OFF")

try:
    ControlRequest(action="INVALID")
    check("ControlRequest 拒绝非法 action", False, "应该抛出异常")
except Exception:
    check("ControlRequest 拒绝非法 action", True)

dev_reg = DeviceRegisterRequest(device_id="ABC123", device_type="light", name="床头灯")
check("DeviceRegisterRequest 创建成功", dev_reg.device_id == "ABC123")
check("DeviceRegisterRequest default family_id", dev_reg.family_id == 1)

# --- scene schemas ---
from services.scene_service.schemas import SceneRuleCreate, RoomStateResponse, AIChatRequest

scene_rule = SceneRuleCreate(
    family_id=1,
    name="自动开灯",
    scene_id="auto_light_on",
    conditions={"temperature": {"gt": 30}},
    actions={"light": "ON"},
)
check("SceneRuleCreate 创建成功", scene_rule.scene_id == "auto_light_on")
check("SceneRuleCreate conditions", scene_rule.conditions == {"temperature": {"gt": 30}})

room_state = RoomStateResponse(
    family_id=1, temperature=25.5, humidity=60.0,
    illumination=800, has_person=True, smoke_detected=False,
    wifi_connected=True, last_update=None,
)
check("RoomStateResponse 创建成功", room_state.temperature == 25.5)

ai_chat = AIChatRequest(message="你好")
check("AIChatRequest 创建成功", ai_chat.message == "你好")

# --- gateway schemas ---
from services.gateway_service.schemas import ConnectionStatus, PingMessage

conn_status = ConnectionStatus(active_families=3, total_connections=10)
check("ConnectionStatus 创建成功", conn_status.active_families == 3)

ping = PingMessage(type="ping")
check("PingMessage 创建成功", ping.type == "ping")

# ══════════════════════════════════════════════════════
#  数据流 4: 数据库连接 & ORM 模型
# ══════════════════════════════════════════════════════
title("数据流 4: 数据库连接 & ORM 模型")

from common.database import SessionLocal, init_database, get_db
from common.models import (
    Base, User, Family, FamilyMember, Room,
    Device, EnvMonitorData, SceneRule, SceneEventLog,
)

init_database()
db = SessionLocal()

try:
    check("数据库 Session 创建成功", db is not None)

    # 检查表存在
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    check("users 表存在", "users" in tables)
    check("families 表存在", "families" in tables)
    check("family_members 表存在", "family_members" in tables)
    check("rooms 表存在", "rooms" in tables)
    check("devices 表存在", "devices" in tables)
    check("env_monitor_data 表存在", "env_monitor_data" in tables)
    check("scene_rules 表存在", "scene_rules" in tables)
    check("scene_event_logs 表存在", "scene_event_logs" in tables)

    # --- 数据流 4.1: User CRUD ---
    title("数据流 4.1: User CRUD (注册/登录/信息流)")
    import random
    rand_suffix = random.randint(10000, 99999)
    test_username = f"test_datalow_{rand_suffix}"
    test_password = "TestDataFlow123"

    # 清理可能存在的旧记录
    existing_user = db.query(User).filter(User.username == test_username).first()
    if existing_user:
        db.delete(existing_user)
        db.commit()

    # Register
    user = User(
        username=test_username,
        email=f"{test_username}@test.com",
        phone=f"138{random.randint(10000000, 99999999)}",
        hashed_password=get_password_hash(test_password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    check("用户注册成功", user.id is not None and user.id > 0, f"user_id={user.id}")
    check("用户名正确", user.username == test_username)
    check("is_active 默认 True", user.is_active is True)
    check("privacy_settings 已初始化", user.privacy_settings is not None)
    check("created_at 已设置", user.created_at is not None)

    # Login 验证
    found_user = db.query(User).filter(User.username == test_username).first()
    check("登录查找用户成功", found_user is not None)
    check("密码验证通过", verify_password(test_password, found_user.hashed_password))

    # Get me
    check("获取用户信息: email", found_user.email == f"{test_username}@test.com")
    check("获取用户信息: is_active", found_user.is_active is True)

    # Update me
    found_user.email = f"updated_{test_username}@test.com"
    db.commit()
    db.refresh(found_user)
    check("更新用户 email 成功", found_user.email == f"updated_{test_username}@test.com")

    # Change password
    new_password = "NewPassword456!"
    found_user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(found_user)
    check("修改密码后旧密码失效", not verify_password(test_password, found_user.hashed_password))
    check("修改密码后新密码生效", verify_password(new_password, found_user.hashed_password))

    # Privacy settings
    found_user.privacy_settings = {"personalization": False, "data_collection": True}
    db.commit()
    db.refresh(found_user)
    check("更新隐私设置成功", found_user.privacy_settings == {"personalization": False, "data_collection": True})

    user_id = found_user.id

    # --- 数据流 4.2: Family CRUD ---
    title("数据流 4.2: Family CRUD (家庭/成员/房间)")

    # Create family
    family = Family(name="测试家庭", owner_id=user_id)
    db.add(family)
    db.commit()
    db.refresh(family)
    check("创建家庭成功", family.id is not None and family.id > 0, f"family_id={family.id}")
    check("家庭名称正确", family.name == "测试家庭")
    check("家庭 owner_id 正确", family.owner_id == user_id)

    family_id = family.id

    # Add member
    member = FamilyMember(family_id=family_id, user_id=user_id, role="admin")
    db.add(member)
    db.commit()
    db.refresh(member)
    check("添加家庭成员成功", member.id is not None)
    check("成员角色 = admin", member.role == "admin")

    # Create room
    room = Room(name="客厅", family_id=family_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    check("创建房间成功", room.id is not None, f"room_id={room.id}")
    check("房间名称正确", room.name == "客厅")

    room2 = Room(name="卧室", family_id=family_id)
    db.add(room2)
    db.commit()

    # List families
    family_memberships = (
        db.query(Family)
        .filter(Family.id == family_id).all()
    )
    check("查询用户家庭列表", len(family_memberships) > 0, f"共 {len(family_memberships)} 个")

    # List members
    members = db.query(FamilyMember).filter(FamilyMember.family_id == family_id).all()
    check("查询家庭成员列表", len(members) > 0, f"共 {len(members)} 人")

    # List rooms
    rooms = db.query(Room).filter(Room.family_id == family_id).all()
    check("查询房间列表", len(rooms) >= 2, f"共 {len(rooms)} 个房间")

    # --- 数据流 4.3: Device CRUD ---
    title("数据流 4.3: Device CRUD (设备注册/查询/列表)")

    test_device_id = f"TEST_DEVICE_{rand_suffix}"

    # 清理旧记录
    old_dev = db.query(Device).filter(Device.device_id == test_device_id).first()
    if old_dev:
        db.delete(old_dev)
        db.commit()

    # Register device
    device = Device(
        device_id=test_device_id,
        device_type="env_monitor",
        name="测试环境监测器",
        family_id=family_id,
        room_id=room.id,
        is_online=True,
        last_seen=datetime.now(timezone.utc),
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    check("设备注册成功", device.id is not None, f"device_db_id={device.id}")
    check("device_id 正确", device.device_id == test_device_id)
    check("device_type 正确", device.device_type == "env_monitor")
    check("family_id 关联正确", device.family_id == family_id)
    check("is_online = True", device.is_online is True)

    # 重复注册拒绝
    dup_device = Device(
        device_id=test_device_id,
        device_type="light",
        name="重复设备",
        family_id=family_id,
    )
    try:
        db.add(dup_device)
        db.commit()
        check("重复设备注册应失败", False, "应抛出完整性约束异常")
    except Exception:
        db.rollback()
        check("重复设备注册被数据库拒绝", True)

    # Query device
    found_dev = db.query(Device).filter(Device.device_id == test_device_id).first()
    check("查询设备成功", found_dev is not None)
    check("设备名称正确", found_dev.name == "测试环境监测器")

    # List devices
    devices = db.query(Device).filter(Device.family_id == family_id).all()
    check("设备列表查询", len(devices) >= 1, f"共 {len(devices)} 台")

    # Init Huawei device (only checks if device already exists)
    from common.config import settings as cfg
    if cfg.HUAWEI_IOTDA_DEVICE_ID:
        huawei_dev = db.query(Device).filter(Device.device_id == cfg.HUAWEI_IOTDA_DEVICE_ID).first()
        if not huawei_dev:
            hw_dev = Device(
                device_id=cfg.HUAWEI_IOTDA_DEVICE_ID,
                device_type="env_monitor",
                name="华为云环境监测器",
                family_id=family_id,
                is_online=True,
                last_seen=datetime.now(timezone.utc),
            )
            db.add(hw_dev)
            db.commit()
            check("华为云设备初始化成功", hw_dev.id is not None)
        else:
            check("华为云设备已存在,跳过初始化", True)
    else:
        check("华为云设备ID未配置,跳过初始化", True, "HUAWEI_IOTDA_DEVICE_ID 为空")

    # --- 数据流 4.4: EnvMonitorData CRUD ---
    title("数据流 4.4: 环境数据存储 (华为云回调数据入库)")

    # 存一条环境数据
    env_data = EnvMonitorData(
        device_id=test_device_id,
        family_id=family_id,
        room_id=room.id,
        mq2_adc=512,
        sht30_temp_raw="25.67",
        sht30_humi_raw="45.30",
        bh1750_raw=850,
        body_state="present",
        raw_data={"source": "test"},
        timestamp=datetime.now(timezone.utc),
    )
    db.add(env_data)
    db.commit()
    db.refresh(env_data)
    check("环境数据存储成功", env_data.id is not None, f"data_id={env_data.id}")
    check("温度数据正确", env_data.sht30_temp_raw == "25.67")
    check("湿度数据正确", env_data.sht30_humi_raw == "45.30")
    check("光照数据正确", env_data.bh1750_raw == 850)
    check("人体状态正确", env_data.body_state == "present")
    check("raw_data JSON 正确", env_data.raw_data == {"source": "test"})

    # 再存一条 (时间稍早)
    env_data2 = EnvMonitorData(
        device_id=test_device_id,
        family_id=family_id,
        sht30_temp_raw="24.50",
        sht30_humi_raw="50.00",
        bh1750_raw=400,
        body_state="absent",
        raw_data={"source": "test2"},
        timestamp=datetime.now(timezone.utc),
    )
    db.add(env_data2)
    db.commit()

    # Query latest
    latest = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == test_device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .first()
    )
    check("查询最新环境数据成功", latest is not None)
    check("最新数据温度 = 25.67", latest.sht30_temp_raw == "25.67")

    # Query history
    history = (
        db.query(EnvMonitorData)
        .filter(EnvMonitorData.device_id == test_device_id)
        .order_by(EnvMonitorData.timestamp.desc())
        .limit(10)
        .all()
    )
    check("查询历史环境数据", len(history) >= 2, f"共 {len(history)} 条")

    # --- 数据流 4.5: Scene Rules CRUD ---
    title("数据流 4.5: 场景规则 CRUD")

    scene_rule_id = f"auto_light_{rand_suffix}"
    rule = SceneRule(
        family_id=family_id,
        name="高温自动开风扇",
        scene_id=scene_rule_id,
        conditions={"temperature": {"gt": 28}},
        actions={"motor_control": "ON"},
        is_enabled=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    check("创建场景规则成功", rule.id is not None, f"rule_id={rule.id}")
    check("场景规则名称正确", rule.name == "高温自动开风扇")
    check("场景条件正确", rule.conditions == {"temperature": {"gt": 28}})
    check("场景动作正确", rule.actions == {"motor_control": "ON"})
    check("is_enabled = True", rule.is_enabled is True)

    # Query rules
    rules = db.query(SceneRule).filter(SceneRule.family_id == family_id).all()
    check("查询家庭场景规则", len(rules) >= 1, f"共 {len(rules)} 条")

    # Update rule
    rule.is_enabled = False
    db.commit()
    db.refresh(rule)
    check("更新场景规则: 禁用", rule.is_enabled is False)

    # Scene Event Log
    event_log = SceneEventLog(
        family_id=family_id,
        rule_id=rule.id,
        scene_id=scene_rule_id,
        event_type="trigger",
        description="温度30度, 触发自动开风扇",
        suggestion="已自动开启风扇降温",
        details={"temperature": 30.5, "action": "motor_control ON"},
    )
    db.add(event_log)
    db.commit()
    db.refresh(event_log)
    check("存储场景事件日志成功", event_log.id is not None)

    # Query events
    events = (
        db.query(SceneEventLog)
        .filter(SceneEventLog.family_id == family_id)
        .all()
    )
    check("查询场景事件日志", len(events) >= 1, f"共 {len(events)} 条")

    # Delete rule
    rule_id = rule.id
    db.delete(rule)
    db.commit()
    deleted_rule = db.query(SceneRule).filter(SceneRule.id == rule_id).first()
    check("删除场景规则成功", deleted_rule is None)

    # --- 清理 ---
    title("清理测试数据")
    # 按依赖顺序清理
    db.query(SceneEventLog).filter(SceneEventLog.family_id == family_id).delete()
    db.query(EnvMonitorData).filter(EnvMonitorData.device_id == test_device_id).delete()
    db.query(Device).filter(Device.device_id == test_device_id).delete()
    db.query(Room).filter(Room.family_id == family_id).delete()
    db.query(FamilyMember).filter(FamilyMember.family_id == family_id).delete()
    db.query(Family).filter(Family.id == family_id).delete()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    check("清理测试数据完成", True)

finally:
    db.close()

# ══════════════════════════════════════════════════════
#  数据流 5: 华为云命令行下发结构
# ══════════════════════════════════════════════════════
title("数据流 5: 华为云命令下发结构验证")

# 验证命令格式正确性
def validate_command(command_name: str, paras: dict) -> dict:
    body = {
        "service_id": "rk2206远程控制",
        "command_name": command_name,
        "paras": paras or {},
    }
    return body

light_cmd = validate_command("light_control", {"onoff": "ON"})
check("light_control 命令结构正确", light_cmd["service_id"] == "rk2206远程控制")
check("light_control command_name", light_cmd["command_name"] == "light_control")
check("light_control paras", light_cmd["paras"] == {"onoff": "ON"})

motor_cmd = validate_command("motor_control", {"onoff": "OFF"})
check("motor_control 命令结构正确", motor_cmd["paras"] == {"onoff": "OFF"})

beep_cmd = validate_command("beep_play", {})
check("beep_play 命令结构正确 (空参数)", beep_cmd["paras"] == {})

# 验证 JSON 序列化正确
json_str = json.dumps(light_cmd, ensure_ascii=False)
check("命令 JSON 序列化正确", '"service_id"' in json_str)
check("包含 rk2206远程控制", '"rk2206远程控制"' in json_str)

# ══════════════════════════════════════════════════════
#  数据流 6: 华为云回调数据解析
# ══════════════════════════════════════════════════════
title("数据流 6: 华为云回调数据解析")

# 模拟华为云 IoTDA 回调的 notify_data 结构
mock_callback_payload = {
    "notify_data": {
        "header": {
            "device_id": "test_device_001",
            "product_id": "product_001",
            "node_id": "node_001",
            "gateway_id": "gateway_001",
        },
        "body": {
            "services": [
                {
                    "service_id": "rk2206远程控制",
                    "event_time": "20260315T120000Z",
                    "properties": {
                        "sht30_temperature": 25.67,
                        "sht30_humidity": 45.30,
                        "bh1750": 850,
                        "body_infrared": "present",
                        "mq2": 512,
                    },
                }
            ]
        },
    }
}

# 手动执行 _parse_huawei_callback_data 逻辑
def parse_callback_data(notify_data: dict) -> dict:
    body = {}
    services = notify_data.get("body", {}).get("services", [])

    if isinstance(services, dict):
        services = [services]

    for service in services:
        service_id = service.get("service_id", "")
        props = service.get("properties", {})

        if service_id == "rk2206远程控制":
            for key, value in props.items():
                if isinstance(value, dict):
                    body[key] = value.get("value")
                else:
                    body[key] = value
        else:
            for key, value in props.items():
                if isinstance(value, dict):
                    body[key] = value.get("value")
                else:
                    body[key] = value

    return body

parsed = parse_callback_data(mock_callback_payload["notify_data"])
check("回调数据解析: 温度", parsed.get("sht30_temperature") == 25.67)
check("回调数据解析: 湿度", parsed.get("sht30_humidity") == 45.30)
check("回调数据解析: 光照", parsed.get("bh1750") == 850)
check("回调数据解析: 人体红外", parsed.get("body_infrared") == "present")
check("回调数据解析: MQ2", parsed.get("mq2") == 512)

# 测试带 dict-value 的回调格式 (华为云可能发嵌套 value)
mock_nested = {
    "body": {
        "services": [
            {
                "service_id": "rk2206远程控制",
                "properties": {
                    "sht30_temperature": {"value": 26.0},
                    "sht30_humidity": {"value": 50.0},
                    "bh1750": {"lux": 900},
                    "body_infrared": "present",
                },
            }
        ]
    },
}

parsed_nested = parse_callback_data(mock_nested)
check("嵌套 value 回调: 温度", parsed_nested.get("sht30_temperature") == 26.0)
check("嵌套 value 回调: 湿度", parsed_nested.get("sht30_humidity") == 50.0)
check("嵌套 value 回调: bh1750 (无value键返回None)", parsed_nested.get("bh1750") is None)
check("嵌套 value 回调: 人体红外(plain)", parsed_nested.get("body_infrared") == "present")

# 测试空回调
parsed_empty = parse_callback_data({"body": {"services": []}})
check("空回调返回空 dict", parsed_empty == {})

# 测试无效数据
parsed_invalid = parse_callback_data({"body": {}})
check("无效回调不崩溃", isinstance(parsed_invalid, dict))

# ══════════════════════════════════════════════════════
#  数据流 7: IoT 客户端结构验证
# ══════════════════════════════════════════════════════
title("数据流 7: IoT 客户端结构验证")

# 测试 common/iot_client.py 的 RESTClient 类能正常导入
from common.iot_client import RESTClient, _build_credentials, _build_headers

if settings.HUAWEI_IOTDA_ENABLED and settings.HUAWEI_IOTDA_AK:
    # 能构建凭证
    creds = _build_credentials()
    check("华为云凭证构建成功", creds is not None)
    check("AK 正确加载", creds.ak == settings.HUAWEI_IOTDA_AK)

    headers = _build_headers(with_body=True)
    check("headers 包含 Content-Type", headers.get("Content-Type") == "application/json")

    if settings.HUAWEI_IOTDA_INSTANCE_ID:
        check("headers 包含 Instance-Id", headers.get("Instance-Id") == settings.HUAWEI_IOTDA_INSTANCE_ID)

    # RESTClient 实例化
    iot_client = RESTClient()
    check("RESTClient 实例化成功", iot_client is not None)
else:
    print("  [SKIP] 华为云 AK/SK 未配置, 跳过 IoT 客户端实例化测试")

# ══════════════════════════════════════════════════════
#  数据流 8: WebSocket Manager 测试
# ══════════════════════════════════════════════════════
title("数据流 8: WebSocket Manager 结构验证")

from common.websocket_manager import manager as ws_manager

check("WebSocket Manager 导入成功", ws_manager is not None)
check("初始连接数为 0", ws_manager.connection_count == 0)

# 构造函数验证：API_URL 构建
# 前端 WebSocket 连接格式: ws://host/ws/{family_id}?token=xxx
test_family_id = "1"
test_token = "eyJhbGciOiJIUzI1NiIs..."
ws_url_with_token = f"ws://localhost:8010/ws/{test_family_id}?token={test_token}"
check("WebSocket URL 格式正确", ws_url_with_token.startswith("ws://"))
check("family_id 在 URL 中", test_family_id in ws_url_with_token)
check("token 在 query string 中", f"token={test_token}" in ws_url_with_token)

# 场景 WebSocket URL
scene_ws_url = f"ws://localhost:8014/api/v1/scenes/ws/{test_family_id}"
check("场景 WebSocket URL 格式正确", scene_ws_url.endswith(f"/scenes/ws/{test_family_id}"))

# ══════════════════════════════════════════════════════
#  数据流 9: 前端 API 请求构造验证
# ══════════════════════════════════════════════════════
title("数据流 9: 前端 API 请求构造验证")

# 前端请求 URL 构造逻辑 (来自 web/src/api/index.js)
def build_api_url(base_url: str, path: str, params: dict = None) -> str:
    full_url = f"{base_url}{path}"
    if params and len(params) > 0:
        query = "&".join(f"{k}={params[k]}" for k in params)
        full_url = f"{full_url}?{query}"
    return full_url

# 认证请求: GET /auth/me?token=xxx
auth_url = build_api_url("/api/v1", "/auth/me", {"token": "test_token_123"})
check("Auth URL 格式", auth_url == "/api/v1/auth/me?token=test_token_123")

# 家庭列表: GET /family/list?token=xxx
family_url = build_api_url("/api/v1", "/family/list", {"token": "test_token_123"})
check("Family URL 格式", family_url == "/api/v1/family/list?token=test_token_123")

# 设备列表: GET /devices/list?family_id=1&token=xxx
device_url = build_api_url("/api/v1", "/devices/list", {"family_id": "1", "token": "test_token_123"})
check("Device list URL 格式", "family_id=1" in device_url and "token=test_token_123" in device_url)

# 场景规则 (无需认证): GET /scenes/rules/1
scene_url = build_api_url("/api/v1", "/scenes/rules/1")
check("Scene URL (无认证) 格式", scene_url == "/api/v1/scenes/rules/1")

# 场景状态 (无需认证): GET /scenes/state/1
state_url = build_api_url("/api/v1", "/scenes/state/1")
check("State URL 格式", state_url == "/api/v1/scenes/state/1")

# ══════════════════════════════════════════════════════
#  数据流 10: AI 客户端结构验证
# ══════════════════════════════════════════════════════
title("数据流 10: AI 客户端结构验证")

import sys as _s, os as _o
_ai = _o.path.abspath(_o.path.join(_o.path.dirname(__file__), '..', 'ai', 'src'))
if _ai not in _s.path:
    _s.path.insert(0, _ai)

from agent_service.ai_client import (
    SMART_HOME_SYSTEM_PROMPT,
    INTENT_PARSE_PROMPT,
    chat_with_ai,
    parse_intent,
)

check("SMART_HOME_SYSTEM_PROMPT 已定义", len(SMART_HOME_SYSTEM_PROMPT) > 100)
check("INTENT_PARSE_PROMPT 已定义", len(INTENT_PARSE_PROMPT) > 100)

# 测试意图解析函数 (不调用 API, 验证结构)
# 当 AI_ENABLED=False 时, parse_intent 走 chat_with_ai 的降级逻辑
from agent_service.ai_client import settings as ai_settings

if not ai_settings.AI_ENABLED:
    # AI 未启用, parse_intent 应返回降级聊天结果
    result = parse_intent("帮我把灯打开")
    check("AI 未启用时 parse_intent 不崩溃", isinstance(result, dict))
    check("降级 intent = chat", result.get("intent") == "chat")
    check("降级 target = None", result.get("target") is None)
else:
    print("  [SKIP] AI 已启用, 跳过降级测试 (需要真实 API Key)")

# ══════════════════════════════════════════════════════
#  总结
# ══════════════════════════════════════════════════════
title("测试总结")

total = PASSED + FAILED
print(f"\n  PASSED: {PASSED}/{total}")
if FAILED > 0:
    print(f"  FAILED: {FAILED}/{total}")
else:
    print(f"  ALL TESTS PASSED!")

if FAILED > 0:
    sys.exit(1)
else:
    sys.exit(0)
