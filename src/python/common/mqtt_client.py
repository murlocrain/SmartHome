"""
华为云IoTDA MQTT订阅客户端
本地主动连接华为云，接收设备上报数据，无需公网IP

数据流：华为云设备 --MQTT推送--> 本地MQTT客户端 --> PostgreSQL --> 前端展示
"""
import json
import ssl
import logging
import threading
import asyncio
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from common.config import settings

logger = logging.getLogger(__name__)


class HuaweiMqttSubscriber:
    """华为云IoTDA MQTT订阅客户端"""

    def __init__(
        self,
        on_message_callback: Optional[Callable] = None,
        family_id: int = 1
    ):
        self.endpoint = settings.HUAWEI_IOTDA_MQTT_ENDPOINT
        self.port = settings.HUAWEI_IOTDA_PORT
        self.device_id = settings.HUAWEI_IOTDA_DEVICE_ID
        self.username = settings.HUAWEI_IOTDA_USERNAME
        self.password = settings.HUAWEI_IOTDA_PASSWORD
        self.client_id = settings.HUAWEI_IOTDA_CLIENT_ID
        self.use_tls = getattr(settings, 'HUAWEI_IOTDA_USE_TLS', True)
        self.family_id = family_id
        self.on_message_callback = on_message_callback
        self.client: Optional[mqtt.Client] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._message_count = 0

    def _get_client(self) -> mqtt.Client:
        """创建并配置MQTT客户端"""
        # clientId格式: {deviceId}_{timestamp}_{mode}
        # mode: 0=直连设备, 1=网关子设备
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
            protocol=mqtt.MQTTv311
        )

        # 设置认证
        client.username_pw_set(self.username, self.password)

        # TLS配置（华为云要求MQTTS）
        if self.use_tls and self.port == 8883:
            context = ssl.create_default_context()
            # 华为云IoTDA使用自签名证书，需要放宽验证
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            client.tls_set_context(context)
            logger.info("MQTT TLS已启用（端口8883）")

        # 回调函数
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        client.on_log = self._on_log

        return client

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        """连接成功回调"""
        if reason_code == 0:
            logger.info(f"MQTT连接成功: {self.endpoint}:{self.port}")
            self._subscribe_topics(client)
        else:
            logger.error(f"MQTT连接失败，错误码: {reason_code}")

    def _subscribe_topics(self, client: mqtt.Client):
        """订阅设备数据相关Topic"""
        did = self.device_id

        # 华为云IoTDA Topic列表
        topics = [
            # 设备属性上报
            f"$oc/devices/{did}/sys/properties/report",
            # 设备属性上报响应
            f"$oc/devices/{did}/sys/properties/report/response",
            # 设备消息上报
            f"$oc/devices/{did}/sys/messages/up",
            # 设备影子变更通知
            f"$oc/devices/{did}/sys/shadow/get/response",
            # 平台下发属性设置响应
            f"$oc/devices/{did}/sys/properties/set/response",
            # 命令下发响应
            f"$oc/devices/{did}/sys/commands/response",
            # 设备异步命令响应
            f"$oc/devices/{did}/sys/commands/request_id/+",
        ]

        for topic in topics:
            result = client.subscribe(topic, qos=1)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"已订阅: {topic}")
            else:
                logger.warning(f"订阅失败: {topic} (错误码: {result[0]})")

    def _on_message(self, client, userdata, msg):
        """收到消息回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8', errors='ignore')
            self._message_count += 1

            logger.debug(f"[{self._message_count}] 收到消息 | Topic: {topic} | 长度: {len(payload)}")

            # 解析JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = {"raw_payload": payload}

            # 添加元信息
            data["_mqtt_topic"] = topic
            data["_device_id"] = self.device_id

            # 调用外部回调处理数据
            if self.on_message_callback:
                self.on_message_callback(data)

        except Exception as e:
            logger.error(f"处理MQTT消息异常: {e}")

    def _on_disconnect(self, client, userdata, reason_code, properties=None):
        """断开连接回调"""
        if reason_code != 0:
            logger.warning(f"MQTT意外断开，错误码: {reason_code}，将自动重连...")
        else:
            logger.info("MQTT正常断开")

    def _on_log(self, client, userdata, level, buf):
        """MQTT日志"""
        if level == mqtt.MQTT_LOG_ERR:
            logger.error(f"MQTT Error: {buf}")
        elif level == mqtt.MQTT_LOG_WARNING:
            logger.warning(f"MQTT Warning: {buf}")

    def start(self, block: bool = False):
        """启动MQTT订阅客户端"""
        if self._running:
            logger.warning("MQTT客户端已在运行中")
            return

        self._running = True
        self.client = self._get_client()

        try:
            logger.info(f"正在连接华为云IoTDA...")
            logger.info(f"  Endpoint: {self.endpoint}:{self.port}")
            logger.info(f"  DeviceId: {self.device_id}")
            logger.info(f"  ClientId: {self.client_id}")

            connect_result = self.client.connect(self.endpoint, self.port, keepalive=60)

            if connect_result != 0:
                logger.error(f"MQTT连接失败，返回码: {connect_result}")
                self._running = False
                return

            self.client.loop_start()

            if block:
                # 阻塞模式，用于独立脚本运行
                try:
                    while self._running:
                        pass
                except KeyboardInterrupt:
                    self.stop()

        except Exception as e:
            logger.error(f"启动MQTT客户端失败: {e}")
            self._running = False
            raise

    def stop(self):
        """停止MQTT订阅客户端"""
        if not self._running:
            return

        self._running = False
        logger.info(f"正在停止MQTT客户端... (共接收 {self._message_count} 条消息)")

        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None

        logger.info("MQTT客户端已停止")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def message_count(self) -> int:
        return self._message_count


# ==================== 全局单例 ====================

_mqtt_subscriber: Optional[HuaweiMqttSubscriber] = None


def get_mqtt_subscriber() -> Optional[HuaweiMqttSubscriber]:
    """获取全局MQTT订阅实例"""
    global _mqtt_subscriber
    return _mqtt_subscriber


def init_mqtt_subscriber(on_message_callback: Optional[Callable] = None, family_id: int = 1) -> HuaweiMqttSubscriber:
    """初始化并启动全局MQTT订阅实例"""
    global _mqtt_subscriber
    _mqtt_subscriber = HuaweiMqttSubscriber(
        on_message_callback=on_message_callback,
        family_id=family_id
    )
    return _mqtt_subscriber


def start_mqtt_subscriber():
    """启动MQTT订阅（非阻塞）"""
    sub = get_mqtt_subscriber()
    if sub:
        sub.start(block=False)


def stop_mqtt_subscriber():
    """停止MQTT订阅"""
    sub = get_mqtt_subscriber()
    if sub:
        sub.stop()
