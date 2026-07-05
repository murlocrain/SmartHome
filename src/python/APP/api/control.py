from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from common.config import settings, logger
from common.control_utils import color_to_int
from common.iot_client import iot_client

router = APIRouter(tags=["设备控制"])


# ============ 请求模型 ============
class LightRequest(BaseModel):
    onoff: Optional[str] = Field(default=None, pattern="^(ON|OFF)$")
    color: Optional[str] = Field(default=None, pattern="^(WHITE|RED|GREEN|BLUE|YELLOW|CYAN|PURPLE)$")
    brightness: Optional[int] = Field(default=None, ge=0, le=255)
    mode: Optional[str] = Field(default=None, pattern="^(STATIC|BREATH)$")

class MotorRequest(BaseModel):
    onoff: Optional[str] = Field(default=None, pattern="^(ON|OFF)$")
    speed: Optional[int] = Field(default=None, ge=0, le=100)

class BeepRequest(BaseModel):
    duration: int = Field(default=2000, ge=1, le=60000)
    frequency: int = Field(default=800, ge=200, le=20000)

class BeepSongRequest(BaseModel):
    id: int = Field(..., ge=0, le=2, description="歌曲ID: 0=两只老虎, 1=熙熙攘攘我们的城市, 2=春日影")

class ModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(morning|read)$")

class LightColorRequest(BaseModel):
    color: str = Field(..., pattern="^(WHITE|RED|GREEN|BLUE|YELLOW|CYAN|PURPLE)$")

class LightBrightnessRequest(BaseModel):
    brightness: int = Field(..., ge=0, le=255)

class LightModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(STATIC|BREATH|NORMAL)$")

class MotorSpeedRequest(BaseModel):
    speed: int = Field(..., ge=0, le=100)


# ============ 内部发送 ============
def _send_command(command_name: str, paras: dict) -> dict:
    if not settings.HUAWEI_IOTDA_ENABLED:
        raise HTTPException(status_code=400, detail="华为云功能未启用")

    result = iot_client.send_command(command_name, paras)
    if result.get("success"):
        return {
            "message": f"{command_name} 命令下发成功",
            "status": "success",
            "command_name": command_name,
            "paras": paras,
        }

    error_msg = result.get("error", "命令下发失败")
    logger.error(f"{command_name} 命令下发失败: {error_msg}")
    raise HTTPException(status_code=500, detail=error_msg)


# ============ 灯光控制（单命令，参数可选） ============
@router.post("/control/light")
def control_light(req: LightRequest):
    paras = {}
    if req.onoff is not None:
        paras["onoff"] = req.onoff
    if req.color is not None:
        paras["color"] = color_to_int(req.color)
    if req.brightness is not None:
        paras["brightness"] = req.brightness
    if req.mode is not None:
        paras["mode"] = req.mode
    logger.info(f"[灯光控制] paras={paras}")
    return _send_command("light_control", paras)


# ============ 电机控制（单命令，参数可选） ============
@router.post("/control/motor")
def control_motor(req: MotorRequest):
    paras = {}
    if req.onoff is not None:
        paras["onoff"] = req.onoff
    if req.speed is not None:
        paras["speed"] = req.speed
    logger.info(f"[电机控制] paras={paras}")
    return _send_command("motor_control", paras)


# ============ 蜂鸣器 ============
@router.post("/control/beep")
def control_beep(req: Optional[BeepRequest] = None):
    paras = {}
    if req:
        paras = {"duration": req.duration, "frequency": req.frequency}
    logger.info(f"[蜂鸣器] paras={paras}")
    return _send_command("beep_play", paras)


# ============ 蜂鸣器歌曲 ============
@router.post("/control/beep_song")
def control_beep_song(req: BeepSongRequest):
    paras = {"id": req.id}
    logger.info(f"[蜂鸣器歌曲] id={req.id}, paras={paras}")
    return _send_command("beep_song", paras)


# ============ 蜂鸣器停止 ============
@router.post("/control/beep_stop")
def control_beep_stop():
    logger.info(f"[蜂鸣器停止]")
    return _send_command("beep_stop", {})


# ============ 快捷模式 ============
@router.post("/control/mode")
def control_mode(req: ModeRequest):
    mode_name = "早间提神模式" if req.mode == "morning" else "阅读模式"
    logger.info(f"[快捷模式] ========== {mode_name}激活开始 ==========")

    if req.mode == "morning":
        logger.info(f"[快捷模式] 早间提神 - 灯光(ON+常亮+绿色)")
        _send_command("light_control", {"onoff": "ON", "mode": "STATIC", "color": "GREEN"})
        logger.info(f"[快捷模式] 早间提神 - 歌曲id=1")
        _send_command("beep_song", {"id": 1})
        logger.info(f"[快捷模式] 早间提神 - 激活蜂鸣器")
        _send_command("beep_play", {})
    else:
        logger.info(f"[快捷模式] 阅读 - 灯光(ON+呼吸灯)")
        _send_command("light_control", {"onoff": "ON", "mode": "BREATH"})
        logger.info(f"[快捷模式] 阅读 - 歌曲id=2")
        _send_command("beep_song", {"id": 2})
        logger.info(f"[快捷模式] 阅读 - 激活蜂鸣器")
        _send_command("beep_play", {})

    logger.info(f"[快捷模式] ========== {mode_name}激活完成 ==========")
    return {
        "message": f"{mode_name}已激活",
        "status": "success",
        "command_name": "mode",
        "paras": {"mode": req.mode},
    }


# ============ 重置所有设备 ============
@router.post("/control/reset")
def control_reset():
    logger.info(f"[重置] ========== 重置所有设备开始 ==========")
    logger.info(f"[重置] 关闭灯光")
    _send_command("light_control", {"onoff": "OFF"})
    logger.info(f"[重置] 停止蜂鸣器")
    _send_command("beep_stop", {})
    logger.info(f"[重置] 切回默认歌曲 id=0")
    _send_command("beep_song", {"id": 0})
    logger.info(f"[重置] 关闭电机")
    _send_command("motor_control", {"onoff": "OFF"})
    logger.info(f"[重置] ========== 重置完成 ==========")
    return {
        "message": "所有设备已重置",
        "status": "success",
        "command_name": "reset",
        "paras": {},
    }


# ============ 灯光子端点（前端分离调用） ============
@router.post("/control/light/color")
def control_light_color(req: LightColorRequest):
    paras = {"color": color_to_int(req.color)}
    logger.info(f"[灯光颜色] paras={paras}")
    return _send_command("light_control", paras)


@router.post("/control/light/brightness")
def control_light_brightness(req: LightBrightnessRequest):
    paras = {"brightness": req.brightness}
    logger.info(f"[灯光亮度] paras={paras}")
    return _send_command("light_control", paras)


@router.post("/control/light/mode")
def control_light_mode(req: LightModeRequest):
    # 前端传 "NORMAL" 映射为 IoTDA 的 "STATIC"
    mode = "STATIC" if req.mode == "NORMAL" else req.mode
    paras = {"mode": mode}
    logger.info(f"[灯光模式] front={req.mode} → iot={mode}")
    return _send_command("light_control", paras)


@router.post("/control/motor/speed")
def control_motor_speed(req: MotorSpeedRequest):
    paras = {"speed": req.speed}
    logger.info(f"[电机速度] paras={paras}")
    return _send_command("motor_control", paras)
