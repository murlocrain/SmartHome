from common.tasks.celery_tasks import celery
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery.task(name='tasks.data.process_environment_data')
def process_environment_data(data: dict):
    """Process incoming environment sensor data"""
    from services.data_collection_service.service import create_environment_data
    try:
        result = create_environment_data(data)
        logger.debug(f"Processed environment data: {data.get('device_id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to process environment data: {e}")
        raise

@celery.task(name='tasks.data.process_radar_data')
def process_radar_data(data: dict):
    """Process incoming radar data"""
    from services.data_collection_service.service import create_radar_data
    try:
        result = create_radar_data(data)
        
        if data.get('motion_detected'):
            logger.info(f"Motion detected by device: {data.get('device_id')}")
            from common.tasks.alert_tasks import trigger_motion_alert
            trigger_motion_alert.delay(data)
        
        return result
    except Exception as e:
        logger.error(f"Failed to process radar data: {e}")
        raise

@celery.task(name='tasks.data.process_event')
def process_event(data: dict):
    """Process incoming event data"""
    from services.data_collection_service.service import create_event
    try:
        result = create_event(data)
        logger.debug(f"Processed event: {data.get('event_type')}")
        return result
    except Exception as e:
        logger.error(f"Failed to process event: {e}")
        raise

@celery.task(name='tasks.data.aggregate_hourly_data')
def aggregate_hourly_data(family_id: int, hour: str = None):
    """Aggregate environment data for an hour"""
    from services.data_analysis_service.service import aggregate_hourly_data
    try:
        if hour is None:
            hour = datetime.now().strftime('%Y-%m-%d %H:00:00')
        result = aggregate_hourly_data(family_id, hour)
        logger.debug(f"Aggregated hourly data for family {family_id} at {hour}")
        return result
    except Exception as e:
        logger.error(f"Failed to aggregate hourly data: {e}")
        raise

@celery.task(name='tasks.data.aggregate_daily_data')
def aggregate_daily_data(family_id: int, date: str = None):
    """Aggregate environment data for a day"""
    from services.data_analysis_service.service import aggregate_daily_data
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        result = aggregate_daily_data(family_id, date)
        logger.info(f"Aggregated daily data for family {family_id} on {date}")
        return result
    except Exception as e:
        logger.error(f"Failed to aggregate daily data: {e}")
        raise

@celery.task(name='tasks.data.cleanup_old_environment_data')
def cleanup_old_environment_data(days_to_keep: int = 30):
    """Clean up old environment data"""
    from services.data_collection_service.service import cleanup_old_environment_data
    try:
        deleted = cleanup_old_environment_data(days_to_keep)
        logger.info(f"Cleaned up {deleted} old environment records")
        return {"deleted": deleted}
    except Exception as e:
        logger.error(f"Failed to cleanup environment data: {e}")
        raise

@celery.task(name='tasks.data.cleanup_old_radar_data')
def cleanup_old_radar_data(days_to_keep: int = 7):
    """Clean up old radar data"""
    from services.data_collection_service.service import cleanup_old_radar_data
    try:
        deleted = cleanup_old_radar_data(days_to_keep)
        logger.info(f"Cleaned up {deleted} old radar records")
        return {"deleted": deleted}
    except Exception as e:
        logger.error(f"Failed to cleanup radar data: {e}")
        raise