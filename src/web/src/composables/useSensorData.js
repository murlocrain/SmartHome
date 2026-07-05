/**
 * 实时传感器数据共享状态
 * 所有页面共享同一份实时数据，通过WebSocket更新
 *
 * 数据格式:
 * {
 *   temperature: number,   // 温度 ℃
 *   humidity: number,      // 湿度 %
 *   light: number,         // 光照 Lux
 *   smoke: number,         // 烟雾浓度 MQ2
 *   pir: boolean,          // 人体检测 有人/无人
 *   wifi: boolean,         // WiFi状态
 *   wifi_rssi: number,     // WiFi信号 RSSI
 *   lightStatus: boolean,  // 灯光状态
 *   motorStatus: boolean,  // 电机状态
 *   ip: number,            // IP地址
 *   voice_command: string, // 最近语音命令
 *   timestamp: string,
 * }
 */

import { ref, reactive } from 'vue'
import WebSocketManager from '@/utils/websocket'

const wsManager = WebSocketManager

// 默认空数据
const defaultData = () => ({
  temperature: null,
  humidity: null,
  light: null,
  smoke: null,
  pir: null,
  wifi: null,
  wifi_rssi: null,
  lightStatus: null,
  motorStatus: null,
  ip: null,
  voice_command: null,
  timestamp: null,
})

// 灯光控制状态
const lightState = reactive({
  onoff: false,
  color: 'WHITE',
  brightness: 180,
  mode: 'STATIC',
})

// 电机控制状态
const motorState = reactive({
  onoff: false,
  speed: 50,
})

// 蜂鸣器状态
const beepState = reactive({
  duration: 1000,
  frequency: 2000,
  playing: false,
})

// 实时传感器数据
const sensorData = reactive(defaultData())
const dataLoaded = ref(false)
const lastUpdateTime = ref(null)

// 灯光/电机状态本地更新（控制命令发送后立即更新UI，WebSocket稍后同步确认）
function updateLightState(patch) {
  // 规范化 onoff: 统一转为 boolean，兼容 string('ON'/'OFF') 和 boolean
  if ('onoff' in patch) {
    const v = patch.onoff
    patch.onoff = v === 'ON' || v === true
  }
  Object.assign(lightState, patch)
  if ('onoff' in patch) sensorData.lightStatus = patch.onoff
}

function updateMotorState(patch) {
  // 规范化 onoff: 统一转为 boolean
  if ('onoff' in patch) {
    const v = patch.onoff
    patch.onoff = v === 'ON' || v === true
  }
  Object.assign(motorState, patch)
  if ('onoff' in patch) sensorData.motorStatus = patch.onoff
}

// WebSocket消息处理
function handleWsMessage(msg) {
  if (msg.type === 'device_update' && msg.data) {
    const d = msg.data
    Object.keys(sensorData).forEach(key => {
      if (d[key] !== undefined) {
        sensorData[key] = d[key]
      }
    })
    lastUpdateTime.value = Date.now()

    // 同步控制状态
    if (d.lightStatus !== undefined) lightState.onoff = d.lightStatus === true
    if (d.motorStatus !== undefined) motorState.onoff = d.motorStatus === true

    dataLoaded.value = true
  }
}

// 连接WebSocket
function connectRealtime(familyId) {
  wsManager.onMessage(handleWsMessage)
  wsManager.connect(String(familyId))
}

// 断开WebSocket
function disconnectRealtime() {
  wsManager.onMessage(null)
}

// 从API初始化数据
function setInitialData(data) {
  if (!data) return
  Object.keys(sensorData).forEach(key => {
    if (data[key] !== undefined && data[key] !== null) {
      sensorData[key] = data[key]
    }
  })
  if (data.lightStatus !== undefined) lightState.onoff = data.lightStatus === true
  if (data.motorStatus !== undefined) motorState.onoff = data.motorStatus === true
  dataLoaded.value = true
  lastUpdateTime.value = Date.now()
}

export {
  sensorData,
  dataLoaded,
  lastUpdateTime,
  lightState,
  motorState,
  beepState,
  updateLightState,
  updateMotorState,
  connectRealtime,
  disconnectRealtime,
  setInitialData,
}
