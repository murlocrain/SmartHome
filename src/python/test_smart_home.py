"""智能家居后端完整测试脚本
两部分:
  1. 直连华为云 IoTDA 下发命令 (不经 HTTP)
  2. 通过 HTTP 接口调用 FastAPI 测试
"""
import json
import sys
import time
import requests

BASE_URL = "http://localhost:8000"

SEP = "=" * 60


def title(text):
    print()
    print(SEP)
    print(f"  {text}")
    print(SEP)


# ============================ 1. 直连华为云 ============================
title("【第 1 部分】直连华为云 IoTDA - 测试 send_command")
try:
    from common.iot_client import iot_client
    from common.config import logger

    # 开灯
    print("\n>>> 发送 light_control / onoff=ON")
    r = iot_client.send_command("light_control", {"onoff": "ON"})
    print(f"    结果: {json.dumps(r, ensure_ascii=False, indent=2)}")
    time.sleep(1)

    # 开风扇
    print("\n>>> 发送 motor_control / onoff=ON")
    r = iot_client.send_command("motor_control", {"onoff": "ON"})
    print(f"    结果: {json.dumps(r, ensure_ascii=False, indent=2)}")
    time.sleep(1)

    # 蜂鸣器
    print("\n>>> 发送 beep_play / 无参数")
    r = iot_client.send_command("beep_play", {})
    print(f"    结果: {json.dumps(r, ensure_ascii=False, indent=2)}")
    time.sleep(1)

    # 关灯
    print("\n>>> 发送 light_control / onoff=OFF")
    r = iot_client.send_command("light_control", {"onoff": "OFF"})
    print(f"    结果: {json.dumps(r, ensure_ascii=False, indent=2)}")
    time.sleep(1)

    # 关风扇
    print("\n>>> 发送 motor_control / onoff=OFF")
    r = iot_client.send_command("motor_control", {"onoff": "OFF"})
    print(f"    结果: {json.dumps(r, ensure_ascii=False, indent=2)}")

except Exception as e:
    print(f"    ❌ 直连测试异常: {e}")


# ============================ 2. HTTP 接口测试 ============================
title("【第 2 部分】通过 HTTP 接口测试")

def post(path, data=None):
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.post(url, json=data or {}, timeout=15)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print(f"    POST {path}")
        print(f"    HTTP {resp.status_code}")
        print(f"    响应: {json.dumps(body, ensure_ascii=False, indent=6) if isinstance(body, (dict, list)) else body}")
        return resp.status_code, body
    except Exception as e:
        print(f"    POST {path} 失败: {e}")
        return 0, str(e)

def get(path):
    url = f"{BASE_URL}{path}"
    try:
        resp = requests.get(url, timeout=10)
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        print(f"    GET {path} -> HTTP {resp.status_code}")
        print(f"    响应: {json.dumps(body, ensure_ascii=False, indent=6) if isinstance(body, (dict, list)) else body}")
        return resp.status_code, body
    except Exception as e:
        print(f"    GET {path} 失败: {e}")
        return 0, str(e)


# 2.1 基础
title("2.1 根路径 + 健康检查")
get("/")
get("/health")

# 2.2 设备控制（严格按照华为云要求的 JSON 格式）
title("2.2 设备控制接口")

post("/control/light", {"action": "ON"})
time.sleep(1)
post("/control/light", {"action": "OFF"})
time.sleep(1)
post("/control/motor", {"action": "ON"})
time.sleep(1)
post("/control/motor", {"action": "OFF"})
time.sleep(1)
post("/control/beep", {})
time.sleep(1)

# 2.3 设备查询
title("2.3 设备查询接口")
get("/devices/list")

# 2.4 AI 接口
title("2.4 AI 对话接口（需在 config.py 配置 API Key）")
post("/ai/chat", {"message": "你好"})

title("2.5 AI 智能体接口（一句话控制设备）")
post("/ai/agent", {"message": "帮我把灯打开"})
time.sleep(1)
post("/ai/agent", {"message": "响一下蜂鸣器"})
time.sleep(1)
post("/ai/agent", {"message": "关灯关风扇"})

title("2.6 AI 环境分析")
post("/ai/analyze-env", {})


title("✅ 全部测试完成")
