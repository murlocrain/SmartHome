/**
 * 全局网络状态跟踪
 * 使用 uni-app 原生 API 检测设备网络连接状态
 *
 * 导出:
 *   isOffline        - ref<boolean>  当前是否离线
 *   networkType      - ref<string>   网络类型 (wifi/4g/5g/none/...)
 *   startMonitoring  - fn()          App 启动时调用一次
 *   stopMonitoring   - fn()          清理监听
 */

import { ref } from 'vue'

// ========== 全局共享状态 ==========
const isOffline = ref(false)
const networkType = ref('unknown')
let _unsubscribe = null
let _initialized = false

// ========== 内部: 网络状态变更回调 ==========
function onStatusChange(res) {
  console.log('[Network] 状态变更:', res.isConnected, res.networkType)
  networkType.value = res.networkType || 'unknown'
  isOffline.value = !res.isConnected

  if (isOffline.value) {
    uni.showToast({ title: '网络已断开', icon: 'none', duration: 2000 })
  } else {
    uni.showToast({ title: '网络已恢复', icon: 'none', duration: 1500 })
  }
}

// ========== 启动网络监听 ==========
function startMonitoring() {
  if (_initialized) return
  _initialized = true

  // 获取当前网络状态
  uni.getNetworkType({
    success(res) {
      networkType.value = res.networkType || 'unknown'
      isOffline.value = res.networkType === 'none'
      console.log('[Network] 当前网络:', res.networkType, '离线:', isOffline.value)
    },
    fail() {
      // 无法获取时假定在线
      isOffline.value = false
    },
  })

  // 监听网络状态变化
  uni.onNetworkStatusChange(onStatusChange)
}

// ========== 停止监听 ==========
function stopMonitoring() {
  if (!_initialized) return
  _initialized = false
  // uni-app 的 onNetworkStatusChange 没有返回取消函数, 只能忽略
  isOffline.value = false
}

// ========== 重新检查网络状态 ==========
function retryNetwork() {
  if (typeof uni !== 'undefined') {
    uni.getNetworkType({
      success(res) {
        networkType.value = res.networkType || 'unknown'
        isOffline.value = res.networkType === 'none'
        if (!isOffline.value) {
          uni.showToast({ title: '网络已恢复', icon: 'none', duration: 1500 })
        }
      },
    })
  }
}

// ========== Composable 供页面使用 ==========
function useNetworkGuard() {
  return {
    isOffline,
    networkType,
    retryNetwork,
  }
}

export { isOffline, networkType, startMonitoring, stopMonitoring, retryNetwork, useNetworkGuard }
