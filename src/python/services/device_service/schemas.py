from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class ControlRequest(BaseModel):
    action: Optional[str] = Field(default=None, pattern="^(ON|OFF)$")
    onoff: Optional[str] = Field(default=None, pattern="^(ON|OFF)$")
    device_id: Optional[str] = None
    brightness: Optional[int] = Field(default=None, ge=0, le=100)
    speed: Optional[int] = Field(default=None, ge=0, le=100)
    direction: Optional[str] = Field(default=None, pattern="^(forward|reverse)$")
    # 蜂鸣器参数
    duration: Optional[int] = Field(default=None, ge=1, le=60000)
    frequency: Optional[int] = Field(default=None, ge=200, le=20000)

    @property
    def onoff_value(self) -> str:
        """统一获取开关值，兼容前端 onoff 和后端 action 两种字段名"""
        val = self.onoff or self.action
        if val is None:
            raise ValueError("action 或 onoff 必须提供且为 ON 或 OFF")
        return val


class DeviceStatusResponse(BaseModel):
    device_id: str
    light_status: Optional[str] = None
    motor_status: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    timestamp: Optional[str] = None


class ControlResponse(BaseModel):
    message: str
    status: str
    command_name: str
    paras: dict


class LightColorRequest(BaseModel):
    color: str = Field(..., pattern="^(WHITE|RED|GREEN|BLUE|YELLOW|CYAN|PURPLE)$")


class LightBrightnessRequest(BaseModel):
    brightness: int = Field(..., ge=0, le=255)


class LightModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(STATIC|BREATH)$")


class MotorSpeedRequest(BaseModel):
    speed: int = Field(..., ge=0, le=100)


class BeepSongRequest(BaseModel):
    id: int = Field(..., ge=0, le=2, description="歌曲ID: 0=两只老虎, 1=熙熙攘攘我们的城市, 2=春日影")


class ModeRequest(BaseModel):
    mode: str = Field(..., pattern="^(morning|read)$", description="模式: morning=早间提神模式, read=阅读模式")


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_type: str = "env_monitor"
    name: Optional[str] = None
    family_id: int = 1


class BindDeviceRequest(BaseModel):
    device_id: str = Field(..., min_length=1, description="设备ID，如 6a2179727f2e6c302f77aaf8_env_monitor_01")
    family_id: int
    name: Optional[str] = None


class DeviceQueryResponse(BaseModel):
    message: str
    device: Optional[dict] = None
    raw_data: Optional[dict] = None


class DeviceListResponse(BaseModel):
    message: str
    count: int = 0
    devices: list = []


class LatestDataResponse(BaseModel):
    message: str
    data: Optional[dict] = None


# ========== 数据分析 ==========
class DataQualityRequest(BaseModel):
    device_id: Optional[str] = None
    hours: int = Field(default=24, ge=1, le=720)


class DataStatsRequest(BaseModel):
    device_id: Optional[str] = None
    field: str = Field(default="sht30_temp_raw")
    hours: int = Field(default=24, ge=1, le=720)
    interval: str = Field(default="hour", pattern="^(minute|hour|day)$")


class DataValidateRequest(BaseModel):
    data: dict


class DataExportRequest(BaseModel):
    format: str = Field(default="json", pattern="^(json|csv)$")
    fields: Optional[str] = None
    device_id: Optional[str] = None
    hours: int = Field(default=24, ge=1, le=720)
    limit: int = Field(default=1000, ge=1, le=10000)
