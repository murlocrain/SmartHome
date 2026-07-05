"""
独立测试脚本：华为云IoTDA MQTT订阅
直接运行即可测试MQTT连接和数据接收，无需启动完整后端

用法:
    python test_mqtt_subscribe.py
"""
import sys
import os
import json
import logging

# 设置项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志输出到控制台
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)

from common.config import settings
from common.mqtt_client import HuaweiMqttSubscriber


def on_message(data: dict):
    """收到消息时的处理"""
    print("\n" + "=" * 60)
    print(f"  收到设备数据！")
    print(f"  Topic: {data.get('_mqtt_topic', 'N/A')}")
    print(f"  DeviceId: {data.get('_device_id', 'N/A')}")

    # 提取services数据
    services = data.get("services", data.get("paras", {}))
    if isinstance(services, list):
        for svc in services:
            props = svc.get("properties", svc.get("paras", {}))
            print(f"\n  服务 [{svc.get('service_id', 'unknown')}]:")
            for k, v in props.items():
                print(f"    {k}: {v}")
    elif isinstance(services, dict):
        print(f"\n  属性数据:")
        for k, v in services.items():
            print(f"    {k}: {v}")

    # 显示原始数据（截断）
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    if len(raw) > 500:
        print(f"\n  原始数据（前500字符）:\n{raw[:500]}...")
    else:
        print(f"\n  原始数据:\n{raw}")

    print("=" * 60)


def main():
    print("=" * 60)
    print("  华为云IoTDA MQTT 订阅测试")
    print("=" * 60)

    print(f"\n[配置信息]")
    print(f"  Endpoint : {settings.HUAWEI_IOTDA_MQTT_ENDPOINT}:{settings.HUAWEI_IOTDA_PORT}")
    print(f"  DeviceId : {settings.HUAWEI_IOTDA_DEVICE_ID}")
    print(f"  Username : {settings.HUAWEI_IOTDA_USERNAME}")
    print(f"  ClientId: {settings.HUAWEI_IOTDA_CLIENT_ID}")
    print(f"  TLS      : {'开启' if settings.HUAWEI_IOTDA_USE_TLS else '关闭'}")

    subscriber = HuaweiMqttSubscriber(
        on_message_callback=on_message,
        family_id=1
    )

    print(f"\n[正在连接...]")
    print(f"  按 Ctrl+C 停止\n")

    try:
        subscriber.start(block=True)
    except KeyboardInterrupt:
        print(f"\n\n用户中断，正在停止...")
    finally:
        subscriber.stop()
        print(f"\n测试结束")


if __name__ == "__main__":
    main()
