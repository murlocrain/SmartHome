from common.tasks.celery_tasks import celery
import logging

logger = logging.getLogger(__name__)

@celery.task(name='tasks.scene.execute_scene_steps')
def execute_scene_steps(scene_id: int, steps: list):
    """Execute scene steps sequentially"""
    from services.scene_service.service import execute_scene_step
    results = []
    
    for step in steps:
        try:
            result = execute_scene_step(step)
            results.append({
                "step": step,
                "success": True,
                "result": result
            })
        except Exception as e:
            logger.error(f"Failed to execute scene step: {e}")
            results.append({
                "step": step,
                "success": False,
                "error": str(e)
            })
    
    return results

@celery.task(name='tasks.scene.schedule_scene')
def schedule_scene(scene_id: int, scheduled_time: str):
    """Schedule a scene to run at a specific time"""
    from services.scene_service.service import schedule_scene
    try:
        result = schedule_scene(scene_id, scheduled_time)
        logger.info(f"Scheduled scene {scene_id} for {scheduled_time}")
        return result
    except Exception as e:
        logger.error(f"Failed to schedule scene: {e}")
        raise

@celery.task(name='tasks.scene.unschedule_scene')
def unschedule_scene(scene_id: int):
    """Unschedule a scene"""
    from services.scene_service.service import unschedule_scene
    try:
        result = unschedule_scene(scene_id)
        logger.info(f"Unscheduled scene {scene_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to unschedule scene: {e}")
        raise

@celery.task(name='tasks.scene.execute_scheduled_scene')
def execute_scheduled_scene(scene_id: int):
    """Execute a scheduled scene"""
    from services.scene_service.service import execute_scene
    try:
        result = execute_scene(scene_id)
        logger.info(f"Executed scheduled scene {scene_id}")
        return result
    except Exception as e:
        logger.error(f"Failed to execute scheduled scene {scene_id}: {e}")
        raise

@celery.task(name='tasks.scene.check_trigger_conditions')
def check_trigger_conditions(scene_id: int):
    """Check if scene trigger conditions are met"""
    from services.scene_service.service import check_trigger_conditions
    try:
        conditions_met = check_trigger_conditions(scene_id)
        if conditions_met:
            execute_scene.delay(scene_id)
            logger.info(f"Trigger conditions met for scene {scene_id}")
        return {"conditions_met": conditions_met}
    except Exception as e:
        logger.error(f"Failed to check trigger conditions: {e}")
        raise