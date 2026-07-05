"""
数据库初始化脚本 - 使用SQLAlchemy自动创建表
"""
import asyncio
from common.database import engine, Base
from services.user_service.models import User, Family, FamilyMember, Room
from services.device_service.models import Device, DeviceGroup, DeviceGroupMember, EnvMonitorData
from services.gateway_service.models import ConnectionLog, MQTTMessageLog
from services.scene_service.models import SceneRule, SceneEventLog


async def init_database():
    print("开始初始化数据库...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("数据库初始化成功!")


if __name__ == "__main__":
    asyncio.run(init_database())
