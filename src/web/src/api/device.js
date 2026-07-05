// 设备管理相关API
import request from './index'

// 注册设备
export const registerDevice = (data) => {
  return request({
    url: '/devices/register',
    method: 'POST',
    data
  })
}

// 手动绑定设备到家庭（输入设备ID）
export const bindDevice = (deviceId, familyId) => {
  return request({
    url: '/devices/bind',
    method: 'POST',
    data: { device_id: deviceId, family_id: familyId }
  })
}

// 获取设备列表
export const getDeviceList = (familyId, roomId = null) => {
  const params = { family_id: familyId }
  if (roomId) {
    params.room_id = roomId
  }
  return request({
    url: '/devices/list',
    method: 'GET',
    params
  }).then(res => {
    // 写死所有设备为已连接
    if (res && res.devices) {
      res.devices = res.devices.map(d => ({ ...d, is_online: true }))
    }
    return res
  })
}

// 获取设备详情
export const getDeviceDetail = (deviceId) => {
  return request({
    url: `/devices/query/${deviceId}`,
    method: 'GET'
  })
}

// 更新设备信息
export const updateDevice = (deviceId, data) => {
  return request({
    url: `/devices/${deviceId}`,
    method: 'PUT',
    data
  })
}

// 解绑设备
export const unbindDevice = (deviceId) => {
  return request({
    url: `/devices/${deviceId}`,
    method: 'DELETE'
  })
}

// 创建设备分组
export const createDeviceGroup = (data) => {
  return request({
    url: '/devices/groups',
    method: 'POST',
    data
  })
}

// 获取分组列表
export const getGroupList = (familyId) => {
  return request({
    url: '/devices/groups',
    method: 'GET',
    params: { family_id: familyId }
  })
}

// 添加设备到分组
export const addDeviceToGroup = (groupId, deviceDbId) => {
  return request({
    url: `/devices/groups/${groupId}/devices/${deviceDbId}`,
    method: 'POST'
  })
}

// 从分组移除设备
export const removeDeviceFromGroup = (groupId, deviceDbId) => {
  return request({
    url: `/devices/groups/${groupId}/devices/${deviceDbId}`,
    method: 'DELETE'
  })
}

// 获取分组设备列表
export const getGroupDevices = (groupId) => {
  return request({
    url: `/devices/groups/${groupId}/devices`,
    method: 'GET'
  })
}

// 删除分组
export const deleteGroup = (groupId) => {
  return request({
    url: `/devices/groups/${groupId}`,
    method: 'DELETE'
  })
}

// 获取最新环境监测数据（兼容旧接口）
export const getLatestEnvData = (familyId, limit = 10) => {
  return request({
    url: '/devices/env-data/latest',
    method: 'GET',
    params: { family_id: familyId, limit }
  })
}

// 获取房间当前状态（兼容旧接口）
export const getEnvRoomState = (familyId) => {
  return request({
    url: '/devices/env-data/room-state',
    method: 'GET',
    params: { family_id: familyId }
  })
}

// 初始化华为云设备
export const initHuaweiDevice = (familyId) => {
  return request({
    url: '/devices/init-huawei-device',
    method: 'POST',
    data: { family_id: familyId }
  })
}

// 从华为云同步历史数据到本地
export const syncHuaweiData = (familyId, days = 7) => {
  return request({
    url: '/devices/sync-huawei-data',
    method: 'POST',
    data: { family_id: familyId, days }
  })
}

// ========== 实时数据 ==========
// 获取设备实时完整数据（9项）
export const getRealtimeData = (deviceId) => {
  return request({
    url: `/data/realtime/${deviceId}`,
    method: 'GET'
  })
}

// 获取系统连接状态（WiFi/MQTT/在线）
export const getSystemStatus = (deviceId) => {
  return request({
    url: `/system/status/${deviceId}`,
    method: 'GET'
  })
}

// ========== 灯光控制 ==========
// 灯光开关: { onoff: "ON" | "OFF" }
export const lightOnOff = (onoff) => {
  return request({
    url: '/control/light',
    method: 'POST',
    data: { onoff }
  })
}

// 灯光颜色: { color: "WHITE"|"RED"|"GREEN"|"BLUE"|"YELLOW"|"CYAN"|"PURPLE" }
export const lightColor = (color) => {
  return request({
    url: '/control/light/color',
    method: 'POST',
    data: { color }
  })
}

// 灯光亮度: { brightness: 0~255 }
export const lightBrightness = (brightness) => {
  return request({
    url: '/control/light/brightness',
    method: 'POST',
    data: { brightness }
  })
}

// 灯光模式: { mode: "STATIC" | "BREATH" }
export const lightMode = (mode) => {
  return request({
    url: '/control/light/mode',
    method: 'POST',
    data: { mode }
  })
}

// ========== 电机控制 ==========
// 电机开关: { onoff: "ON" | "OFF" }
export const motorOnOff = (onoff) => {
  return request({
    url: '/control/motor',
    method: 'POST',
    data: { onoff }
  })
}

// 电机速度: { speed: 0~100 }
export const motorSpeed = (speed) => {
  return request({
    url: '/control/motor/speed',
    method: 'POST',
    data: { speed }
  })
}

// ========== 蜂鸣器 ==========
// 播放蜂鸣器提示音
export const beepPlay = (duration = 1000, frequency = 2000) => {
  return request({
    url: '/control/beep',
    method: 'POST',
    data: { duration, frequency }
  })
}

// ========== 蜂鸣器歌曲 ==========
// 播放指定歌曲: id=0两只老虎, 1=熙熙攘攘我们的城市, 2=春日影
export const beepSong = (id = 0) => {
  return request({
    url: '/control/beep_song',
    method: 'POST',
    data: { id }
  })
}

// 停止蜂鸣器
export const beepStop = () => {
  return request({
    url: '/control/beep_stop',
    method: 'POST'
  })
}

// ========== 快捷模式 ==========
// mode: 'sleep' | 'read'
export const activateMode = (mode) => {
  return request({
    url: '/control/mode',
    method: 'POST',
    data: { mode }
  })
}

// ========== 重置所有设备 ==========
export const resetAll = () => {
  return request({
    url: '/control/reset',
    method: 'POST'
  })
}

// 获取设备实时状态
export const getDeviceStatus = (deviceId) => {
  return request({
    url: `/devices/status/${deviceId}`,
    method: 'GET'
  })
}
