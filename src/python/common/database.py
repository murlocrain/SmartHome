import time as _time
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from common.config import settings, logger
from common.models import (
    Base,
    User,
    Family,
    Room,
    Device,
    EnvMonitorData,
    AIPrediction,
)


def create_database_engine():
    if settings.DATABASE_TYPE.lower() == "mysql":
        try:
            import pymysql
            conn = pymysql.connect(
                host=settings.MYSQL_HOST,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                port=settings.MYSQL_PORT,
                connect_timeout=3,
            )
            conn.close()

            conn = pymysql.connect(
                host=settings.MYSQL_HOST,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                port=settings.MYSQL_PORT,
            )
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DB} "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.close()

            engine = create_engine(
                f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
                f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4"
            )
            logger.info(
                f"成功连接到MySQL数据库: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
            )
            return engine
        except Exception as e:
            logger.warning(f"无法连接MySQL，回退到SQLite: {e}")

    engine = create_engine(f"sqlite:///{settings.DATABASE_PATH}")
    logger.info(f"使用SQLite数据库: {settings.DATABASE_PATH}")
    return engine


engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate_ai_predictions():
    """重建 ai_predictions 表，确保字段与模型定义一致。旧数据会丢失，但在开发阶段可接受。"""
    try:
        from sqlalchemy import text, inspect
        from common.models import AIPrediction
        inspector = inspect(engine)
        expected_cols = {c.name for c in AIPrediction.__table__.columns}

        if "ai_predictions" not in inspector.get_table_names():
            AIPrediction.__table__.create(bind=engine)
            logger.info("ai_predictions 表已创建")
            return

        existing_cols = {c["name"] for c in inspector.get_columns("ai_predictions")}
        if existing_cols == expected_cols:
            logger.info("ai_predictions 表结构一致，跳过迁移")
            return

        logger.warning(f"ai_predictions 表结构不一致，删除重建... (现有: {existing_cols}, 期望: {expected_cols})")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS ai_predictions"))
            conn.commit()
        AIPrediction.__table__.create(bind=engine)
        logger.info("ai_predictions 表重建完成")
    except Exception as e:
        logger.warning(f"AI预测表迁移跳过: {e}")


def init_database():
    # 多进程并发启动可能导致 "concurrent DDL" 错误，重试即可
    for attempt in range(3):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except Exception as e:
            if attempt < 2:
                logger.info(f"表初始化并发冲突，1秒后重试 ({attempt + 1}/3): {e}")
                _time.sleep(1)
            else:
                logger.warning(f"表初始化失败（已重试3次）: {e}")
    logger.info("数据库表初始化完成")

    _migrate_ai_predictions()

    from common.security import get_password_hash

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                phone="13800138000",
                hashed_password=get_password_hash("admin123"),
            )
            db.add(admin)
            db.commit()
            logger.info("默认用户创建完成 (用户名: admin, 密码: admin123)")
        else:
            # 确保 admin 密码哈希有效（旧数据库可能有无效哈希）
            admin.hashed_password = get_password_hash("admin123")
            db.commit()
            logger.info("admin 用户密码已刷新")

        admin = db.query(User).filter(User.username == "admin").first()
        if admin and not db.query(Family).filter(Family.name == "默认家庭").first():
            family = Family(name="默认家庭", owner_id=admin.id)
            db.add(family)
            db.commit()
            logger.info("默认家庭创建完成")

        family = db.query(Family).filter(Family.name == "默认家庭").first()
        if family and not db.query(Room).filter(Room.name == "客厅").first():
            room = Room(name="客厅", family_id=family.id)
            db.add(room)
            db.commit()
            logger.info("默认房间创建完成")
    finally:
        db.close()
