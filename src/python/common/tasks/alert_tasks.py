from common.tasks.celery_tasks import celery
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@celery.task(name='tasks.alert.trigger_motion_alert')
def trigger_motion_alert(data: dict):
    """Trigger motion detection alert"""
    from services.security_service.service import create_alert
    try:
        alert_data = {
            "alert_type": "motion_detection",
            "severity": "info",
            "device_id": data.get("device_id"),
            "message": f"Motion detected by device {data.get('device_id')}",
            "details": {
                "distance": data.get("distance"),
                "timestamp": data.get("timestamp")
            }
        }
        result = create_alert(alert_data)
        logger.info(f"Created motion alert: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to create motion alert: {e}")
        raise

@celery.task(name='tasks.alert.trigger_temperature_alert')
def trigger_temperature_alert(device_id: str, temperature: float, threshold: float, is_high: bool):
    """Trigger temperature alert"""
    from services.security_service.service import create_alert
    try:
        alert_type = "temperature_high" if is_high else "temperature_low"
        message = f"Temperature {'exceeds' if is_high else 'below'} threshold: {temperature}C (threshold: {threshold}C)"
        
        alert_data = {
            "alert_type": alert_type,
            "severity": "warning",
            "device_id": device_id,
            "message": message,
            "details": {
                "temperature": temperature,
                "threshold": threshold,
                "is_high": is_high
            }
        }
        result = create_alert(alert_data)
        logger.info(f"Created temperature alert: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to create temperature alert: {e}")
        raise

@celery.task(name='tasks.alert.trigger_co2_alert')
def trigger_co2_alert(device_id: str, co2_level: int, threshold: int):
    """Trigger CO2 level alert"""
    from services.security_service.service import create_alert
    try:
        alert_data = {
            "alert_type": "co2_high",
            "severity": "warning",
            "device_id": device_id,
            "message": f"CO2 level exceeds threshold: {co2_level}ppm (threshold: {threshold}ppm)",
            "details": {
                "co2_level": co2_level,
                "threshold": threshold
            }
        }
        result = create_alert(alert_data)
        logger.info(f"Created CO2 alert: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to create CO2 alert: {e}")
        raise

@celery.task(name='tasks.alert.trigger_device_offline')
def trigger_device_offline(device_id: str, last_seen: str = None):
    """Trigger device offline alert"""
    from services.security_service.service import create_alert
    try:
        alert_data = {
            "alert_type": "device_offline",
            "severity": "error",
            "device_id": device_id,
            "message": f"Device {device_id} is offline",
            "details": {
                "last_seen": last_seen or datetime.now().isoformat()
            }
        }
        result = create_alert(alert_data)
        logger.info(f"Created device offline alert: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to create device offline alert: {e}")
        raise

@celery.task(name='tasks.alert.trigger_system_alert')
def trigger_system_alert(message: str, severity: str = "info", details: dict = None):
    """Trigger system alert"""
    from services.security_service.service import create_alert
    try:
        alert_data = {
            "alert_type": "system",
            "severity": severity,
            "message": message,
            "details": details or {}
        }
        result = create_alert(alert_data)
        logger.info(f"Created system alert: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to create system alert: {e}")
        raise

@celery.task(name='tasks.alert.acknowledge_alert')
def acknowledge_alert(alert_id: int, user_id: int):
    """Acknowledge an alert"""
    from services.security_service.service import acknowledge_alert
    try:
        result = acknowledge_alert(alert_id, user_id)
        logger.info(f"Acknowledged alert {alert_id} by user {user_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise

@celery.task(name='tasks.alert.process_alerts')
def process_alerts(alerts: list):
    """Process multiple alerts"""
    results = []
    for alert in alerts:
        try:
            from services.security_service.service import create_alert
            result = create_alert(alert)
            results.append({"success": True, "result": result})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
    return results