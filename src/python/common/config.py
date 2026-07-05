"""应用配置 — 敏感信息通过 .env 环境变量注入，不要硬编码。"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Settings:
    # ========== 项目基本信息 ==========
    PROJECT_NAME = os.getenv("PROJECT_NAME", "Smart Home IoT Platform")
    VERSION = os.getenv("VERSION", "1.0.0")
    API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")

    # ========== JWT 认证 ==========
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ========== CORS ==========
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # ========== 华为云 IoTDA ==========
    HUAWEI_IOTDA_ENABLED = os.getenv("HUAWEI_IOTDA_ENABLED", "true").lower() == "true"

    HUAWEI_IOTDA_REST_ENDPOINT = os.getenv("HUAWEI_IOTDA_REST_ENDPOINT", "iotda.cn-north-4.myhuaweicloud.com")
    HUAWEI_IOTDA_APP_ENDPOINT = os.getenv("HUAWEI_IOTDA_APP_ENDPOINT", "")

    HUAWEI_IOTDA_MQTT_ENDPOINT = os.getenv("HUAWEI_IOTDA_MQTT_ENDPOINT", "")
    HUAWEI_IOTDA_PORT = int(os.getenv("HUAWEI_IOTDA_PORT", "8883"))
    HUAWEI_IOTDA_DEVICE_ID = os.getenv("HUAWEI_IOTDA_DEVICE_ID", "")
    HUAWEI_IOTDA_USERNAME = os.getenv("HUAWEI_IOTDA_USERNAME", "")
    HUAWEI_IOTDA_PASSWORD = os.getenv("HUAWEI_IOTDA_PASSWORD", "")
    HUAWEI_IOTDA_CLIENT_ID = os.getenv("HUAWEI_IOTDA_CLIENT_ID", "")
    HUAWEI_IOTDA_USE_TLS = os.getenv("HUAWEI_IOTDA_USE_TLS", "true").lower() == "true"

    HUAWEI_IOTDA_AK = os.getenv("HUAWEI_IOTDA_AK", "")
    HUAWEI_IOTDA_SK = os.getenv("HUAWEI_IOTDA_SK", "")
    HUAWEI_IOTDA_PROJECT_ID = os.getenv("HUAWEI_IOTDA_PROJECT_ID", "")
    HUAWEI_IOTDA_INSTANCE_ID = os.getenv("HUAWEI_IOTDA_INSTANCE_ID", "")

    HUAWEI_IOTDA_REST_ENABLED = os.getenv("HUAWEI_IOTDA_REST_ENABLED", "false").lower() == "true"
    SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", "30"))

    # ========== 数据库 ==========
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "mysql")

    DATABASE_PATH = os.getenv("DATABASE_PATH", "smart_home.db")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "smart_home")

    # ========== AI 智能体（OpenAI 兼容协议） ==========
    AI_ENABLED = os.getenv("AI_ENABLED", "false").lower() == "true"
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
    AI_MODEL = os.getenv("AI_MODEL", "deepseek-chat")
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))


settings = Settings()
