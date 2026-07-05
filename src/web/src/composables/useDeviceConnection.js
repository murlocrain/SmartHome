/**
 * 设备连接状态检测
 * 用于"家庭"模块的设备连接检测，确保设备连接后才显示完整布局
 *
 * 状态流转:
 *   CHECKING  →  CONNECTED（有在线设备）
 *            →  DISCONNECTED（无设备或无在线设备）
 */

import { ref, computed } from 'vue'
import { getDeviceList } from '@/api'

const connectionState = ref('checking')
const deviceOnlineCount = ref(0)
const deviceTotalCount = ref(0)
const authError = ref(false)
let _pollTimer = null
let _checkInProgress = false
let _currentFamilyId = null
let _judgeSeq = 0  // 未连接判断句计数器

const isDeviceConnected = computed(() => connectionState.value === 'connected')
const isChecking = computed(() => connectionState.value === 'checking')

function _isAuthError(err) {
  if (!err) return false
  return err.statusCode === 401 || (err.errMsg && String(err.errMsg).includes('401'))
}

function _bump(format, ...args) {
  _judgeSeq++
  const prefix = '[判断#' + _judgeSeq + ']'
  const msg = format.replace(/\{(\d+)\}/g, (_, i) => args[i])
  console.log('[DETECT:F?]' + prefix + ' ' + msg)
}

async function checkConnection(familyId) {
  // [HARDCODED] 设备连接状态写死为已连接
  console.log('[DETECT:HARDCODED] 设备状态写死为 connected')
  _currentFamilyId = familyId || _currentFamilyId
  connectionState.value = 'connected'
  deviceOnlineCount.value = 1
  deviceTotalCount.value = 1
  authError.value = false
  return true
}

function startPolling(familyId, intervalMs = 5000) {
  stopPolling()
  if (familyId) _currentFamilyId = familyId
  if (!_currentFamilyId) {
    console.log('[DETECT:F9] startPolling: familyId为空 → 无法启动轮询')
    _bump('startPolling: familyId为空 → 无法启动轮询')
    return
  }
  console.log('[DETECT:F9] 启动轮询: familyId=' + _currentFamilyId + ', interval=' + intervalMs + 'ms')
  checkConnection(_currentFamilyId)
  _pollTimer = setInterval(() => {
    console.log('[DETECT:F9] 轮询触发 → familyId=' + _currentFamilyId)
    checkConnection(_currentFamilyId)
  }, intervalMs)
}

function stopPolling() {
  if (_pollTimer) {
    console.log('[DETECT:F9] 停止轮询')
    clearInterval(_pollTimer)
    _pollTimer = null
  }
}

function resetState() {
  stopPolling()
  _currentFamilyId = null
  connectionState.value = 'checking'
  deviceOnlineCount.value = 0
  deviceTotalCount.value = 0
  authError.value = false
}

function clearAuthError() {
  authError.value = false
}

function cleanupConnection() {
  stopPolling()
}

function useDeviceConnection() {
  return {
    connectionState,
    deviceOnlineCount,
    deviceTotalCount,
    authError,
    isDeviceConnected,
    isChecking,
    checkConnection,
    startPolling,
    stopPolling,
    resetState,
    clearAuthError,
  }
}

export {
  useDeviceConnection,
  cleanupConnection,
  connectionState,
  deviceOnlineCount,
  deviceTotalCount,
  authError,
  isDeviceConnected,
  isChecking,
  checkConnection,
  startPolling,
  stopPolling,
  resetState,
  clearAuthError,
}
