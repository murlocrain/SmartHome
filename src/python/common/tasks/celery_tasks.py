from celery import Celery
from common.config import settings
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

celery = Celery(
    'smarthome_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'common.tasks.data_tasks',
        'common.tasks.scene_tasks',
        'common.tasks.alert_tasks',
    ]
)

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
)

@celery.task(bind=True, name='tasks.heartbeat')
def heartbeat(self):
    """Heartbeat task to keep workers alive"""
    logger.info(f"Heartbeat from worker {self.request.id}")
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@celery.task(name='tasks.scheduled_cleanup')
def scheduled_cleanup(days_to_keep=30):
    """Clean up old data from database"""
    from services.data_collection_service.service import cleanup_old_data
    try:
        deleted = cleanup_old_data(days_to_keep)
        logger.info(f"Cleaned up {deleted} old records")
        return {"deleted": deleted}
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {"error": str(e)}

@celery.task(name='tasks.generate_daily_report')
def generate_daily_report(family_id: int):
    """Generate daily report for a family"""
    from services.data_analysis_service.service import generate_daily_report
    try:
        report = generate_daily_report(family_id)
        logger.info(f"Generated daily report for family {family_id}")
        return report
    except Exception as e:
        logger.error(f"Daily report generation failed: {e}")
        return {"error": str(e)}

@celery.task(name='tasks.execute_scene')
def execute_scene(scene_id: int):
    """Execute a scene asynchronously"""
    from services.scene_service.service import execute_scene
    try:
        result = execute_scene(scene_id)
        logger.info(f"Executed scene {scene_id}")
        return result
    except Exception as e:
        logger.error(f"Scene execution failed: {e}")
        return {"error": str(e)}

@celery.task(name='tasks.process_device_command')
def process_device_command(device_id: int, command: dict):
    """Process device command asynchronously"""
    from services.device_service.service import control_device
    try:
        result = control_device(device_id, command)
        logger.info(f"Processed command for device {device_id}")
        return result
    except Exception as e:
        logger.error(f"Device command processing failed: {e}")
        return {"error": str(e)}

@celery.task(name='tasks.check_security_rules')
def check_security_rules(family_id: int):
    """Check security rules for a family"""
    from services.security_service.service import check_all_rules
    try:
        alerts = check_all_rules(family_id)
        logger.info(f"Checked security rules for family {family_id}, {len(alerts)} alerts")
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Security rules check failed: {e}")
        return {"error": str(e)}

@celery.task(name='tasks.refresh_recommendations')
def refresh_recommendations(user_id: int):
    """Refresh recommendations for a user"""
    from services.recommendation_service.service import refresh_user_recommendations
    try:
        recommendations = refresh_user_recommendations(user_id)
        logger.info(f"Refreshed recommendations for user {user_id}")
        return recommendations
    except Exception as e:
        logger.error(f"Recommendation refresh failed: {e}")
        return {"error": str(e)}

# Periodic tasks
celery.conf.beat_schedule = {
    'heartbeat-every-60-seconds': {
        'task': 'tasks.heartbeat',
        'schedule': timedelta(seconds=60),
    },
    'cleanup-daily': {
        'task': 'tasks.scheduled_cleanup',
        'schedule': timedelta(days=1),
        'args': (30,),
    },
}

if __name__ == '__main__':
    celery.start()