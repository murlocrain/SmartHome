<template>
  <view class="page">
    <!-- 桌面端左侧边栏占位 -->
    <view v-if="isDesktop" class="sidebar-spacer"></view>

    <CustomTabBar v-if="isDesktop" :current-index="0" />

    <view class="page-content" :class="{ 'desktop-content': isDesktop }">
      <NetworkGuard v-if="isOffline" :state="'offline'" @retry="retryNetwork" />
      <NetworkGuard v-else-if="authError" :state="'unauthorized'" @retry="retryAuth" />
      <NetworkGuard v-else-if="!isDeviceConnected" :state="connectionState" @retry="retryCheck" />

      <template v-else>
        <!-- 页面标题 -->
        <view class="page-header">
          <text class="header-title">环境监测</text>
          <view class="header-status">
            <view class="status-dot online"></view>
            <text class="status-text">实时在线</text>
          </view>
        </view>

        <!-- 快捷模式 -->
        <view class="mode-section">
          <view class="mode-section-header">
            <text class="mode-section-title">快捷模式</text>
            <view class="reset-btn" :class="{ loading: modeLoading === 'reset' }" @tap="handleReset">
              <text class="reset-btn-icon">🔄</text>
              <text class="reset-btn-text">重置</text>
            </view>
          </view>
          <view class="mode-buttons">
            <view class="mode-btn morning-mode" :class="{ loading: modeLoading === 'morning' }" @tap="activateMorningMode">
                <text class="mode-btn-icon">☀️</text>
                <text class="mode-btn-name">早间提神</text>
                <text class="mode-btn-desc">绿色灯光+音乐</text>
              </view>
            <view class="mode-btn read-mode" :class="{ loading: modeLoading === 'read' }" @tap="activateReadMode">
              <text class="mode-btn-icon">📖</text>
              <text class="mode-btn-name">阅读模式</text>
              <text class="mode-btn-desc">呼吸灯 · 音乐</text>
            </view>
          </view>
        </view>

        <!-- 刷新提示 -->
        <view v-if="refreshing" class="refresh-tip">
          <text class="refresh-text">⏳ 数据刷新中...</text>
        </view>

        <!-- 数据卡片网格 -->
        <view class="sensor-grid">
          <!-- 温度 -->
          <view class="sensor-card temp-card" @tap="manualRefresh">
            <view class="card-icon">🌡️</view>
            <view class="card-info">
              <text class="card-value" v-if="sensorData.temperature !== null">{{ sensorData.temperature }}<text class="card-unit">℃</text></text>
              <text class="card-value placeholder" v-else>--<text class="card-unit">℃</text></text>
              <text class="card-label">温度</text>
            </view>
          </view>

          <!-- 湿度 -->
          <view class="sensor-card humi-card" @tap="manualRefresh">
            <view class="card-icon">💧</view>
            <view class="card-info">
              <text class="card-value" v-if="sensorData.humidity !== null">{{ sensorData.humidity }}<text class="card-unit">%</text></text>
              <text class="card-value placeholder" v-else>--<text class="card-unit">%</text></text>
              <text class="card-label">湿度</text>
            </view>
          </view>

          <!-- 光照 -->
          <view class="sensor-card light-card" @tap="manualRefresh">
            <view class="card-icon">☀️</view>
            <view class="card-info">
              <text class="card-value" v-if="sensorData.light !== null">{{ sensorData.light }}<text class="card-unit">Lux</text></text>
              <text class="card-value placeholder" v-else>--<text class="card-unit">Lux</text></text>
              <text class="card-label">光照</text>
            </view>
          </view>

          <!-- 烟雾 -->
          <view class="sensor-card smoke-card" :class="{ 'alert': sensorData.smoke !== null && sensorData.smoke > 500 }" @tap="manualRefresh">
            <view class="card-icon">🔥</view>
            <view class="card-info">
              <text class="card-value" v-if="sensorData.smoke !== null">{{ sensorData.smoke }}</text>
              <text class="card-value placeholder" v-else>--</text>
              <text class="card-label">烟雾浓度</text>
            </view>
          </view>

          <!-- 人体检测 -->
          <view class="sensor-card status-card" :class="{ 'active': sensorData.pir }">
            <view class="card-icon">{{ sensorData.pir ? '🚶' : '👤' }}</view>
            <view class="card-info">
              <text class="card-value" :class="statusClass(sensorData.pir)">{{ sensorData.pir === null ? '--' : (sensorData.pir ? '有人' : '无人') }}</text>
              <text class="card-label">人体检测</text>
            </view>
          </view>

          <!-- WiFi状态 -->
          <view class="sensor-card status-card" :class="{ 'active': sensorData.wifi }">
            <view class="card-icon">{{ sensorData.wifi ? '📶' : '❌' }}</view>
            <view class="card-info">
              <text class="card-value" :class="statusClass(sensorData.wifi)">{{ sensorData.wifi === null ? '--' : (sensorData.wifi ? '已连接' : '未连接') }}</text>
              <text class="card-label">WiFi状态</text>
            </view>
          </view>

          <!-- WiFi信号 -->
          <view class="sensor-card status-card" :class="{ 'active': sensorData.wifi }">
            <view class="card-icon">📡</view>
            <view class="card-info">
              <text class="card-value" v-if="sensorData.wifi_rssi !== null">{{ sensorData.wifi_rssi }}<text class="card-unit">dBm</text></text>
              <text class="card-value placeholder" v-else>--<text class="card-unit">dBm</text></text>
              <text class="card-label">WiFi信号</text>
            </view>
          </view>

          <!-- 灯光状态 -->
          <view class="sensor-card status-card" :class="{ 'active': sensorData.lightStatus }" @tap="navToLight">
            <view class="card-icon">{{ sensorData.lightStatus ? '💡' : '🔦' }}</view>
            <view class="card-info">
              <text class="card-value" :class="statusClass(sensorData.lightStatus)">{{ sensorData.lightStatus === null ? '--' : (sensorData.lightStatus ? '开启' : '关闭') }}</text>
              <text class="card-label">灯光状态</text>
            </view>
          </view>

          <!-- 电机状态 -->
          <view class="sensor-card status-card" :class="{ 'active': sensorData.motorStatus }" @tap="navToMotor">
            <view class="card-icon">{{ sensorData.motorStatus ? '⚙️' : '🔧' }}</view>
            <view class="card-info">
              <text class="card-value" :class="statusClass(sensorData.motorStatus)">{{ sensorData.motorStatus === null ? '--' : (sensorData.motorStatus ? '开启' : '关闭') }}</text>
              <text class="card-label">电机状态</text>
            </view>
          </view>
        </view>

        <!-- 最后更新时间 -->
        <view class="last-update" v-if="lastUpdateTime">
          <text class="update-text">最后更新: {{ updateTimeText }}</text>
        </view>
      </template>
    </view>

    <!-- 移动端底部TabBar占位 -->
    <view v-if="!isDesktop" class="tabbar-spacer"></view>
    <CustomTabBar v-if="!isDesktop" :current-index="0" />

    <!-- AI 助手浮动入口 -->
    <AiAssistant />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { useNetworkGuard } from '@/composables/useNetwork.js'
import { useDeviceConnection, cleanupConnection } from '@/composables/useDeviceConnection'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { getRealtimeData } from '@/api/device'
import { activateMode, resetAll } from '@/api/device'
import {
  sensorData,
  dataLoaded,
  lastUpdateTime,
  connectRealtime,
  disconnectRealtime,
  setInitialData,
} from '@/composables/useSensorData'
import CustomTabBar from '@/components/CustomTabBar.vue'
import NetworkGuard from '@/components/NetworkGuard.vue'
import AiAssistant from '@/components/AiAssistant.vue'

const { isOffline, retryNetwork } = useNetworkGuard()
const { isDesktop } = useBreakpoint()
const { connectionState, isDeviceConnected, authError, checkConnection, startPolling, stopPolling, clearAuthError } = useDeviceConnection()

const refreshing = ref(false)
const modeLoading = ref(null)  // 'sleep' | 'read' | null

const updateTimeText = computed(() => {
  if (!lastUpdateTime.value) return '--'
  const d = new Date(lastUpdateTime.value)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
})

const statusClass = (val) => {
  if (val === null || val === undefined) return 'placeholder'
  return val ? 'status-on' : 'status-off'
}

function navToLight() {
  uni.switchTab({ url: '/pages/devices/index' })
}

function navToMotor() {
  uni.switchTab({ url: '/pages/scenes/index' })
}

async function fetchData() {
  try {
    refreshing.value = true
    const familyInfo = uni.getStorageSync('selectedFamily')
    if (!familyInfo) {
      refreshing.value = false
      return
    }
    const deviceId = familyInfo.huawei_device_id || familyInfo.device_id
    if (!deviceId) {
      refreshing.value = false
      return
    }
    const res = await getRealtimeData(deviceId)
    if (res && res.data) {
      setInitialData(res.data)
    }
  } catch (e) {
    console.error('获取实时数据失败', e)
  } finally {
    refreshing.value = false
  }
}

async function manualRefresh() {
  await fetchData()
  uni.showToast({ title: '数据已刷新', icon: 'none', duration: 1000 })
}

async function retryCheck() {
  await fetchData()
}

async function retryAuth() {
  // 清除认证错误并重新检测
  clearAuthError()
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) {
    checkConnection(familyInfo.family_id)
  }
}

// 早间提神模式：绿色灯光 + 播放"熙熙攘攘我们的城市"
async function activateMorningMode() {
  if (modeLoading.value) return
  modeLoading.value = 'morning'
  try {
    await activateMode('morning')
    uni.showToast({ title: '早间提神模式已开启', icon: 'success' })
  } catch (e) {
    console.error('早间提神模式激活失败:', e)
    uni.showToast({ title: '模式切换失败', icon: 'error' })
  } finally {
    modeLoading.value = null
  }
}

// 阅读模式：呼吸灯 + 播放"春日影"
async function activateReadMode() {
  if (modeLoading.value) return
  modeLoading.value = 'read'
  try {
    await activateMode('read')
    uni.showToast({ title: '阅读模式已开启', icon: 'success' })
  } catch (e) {
    console.error('阅读模式激活失败:', e)
    uni.showToast({ title: '模式切换失败', icon: 'error' })
  } finally {
    modeLoading.value = null
  }
}

// 重置所有设备
async function handleReset() {
  if (modeLoading.value) return
  modeLoading.value = 'reset'
  try {
    await resetAll()
    uni.showToast({ title: '设备已全部重置', icon: 'success' })
  } catch (e) {
    console.error('重置失败:', e)
    uni.showToast({ title: '重置失败', icon: 'error' })
  } finally {
    modeLoading.value = null
  }
}

onMounted(() => {
  fetchData()
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) {
    connectRealtime(familyInfo.family_id)
    startPolling(familyInfo.family_id)
  }
})

onUnmounted(() => {
  stopPolling()
})

onShow(() => {
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) {
    if (!authError.value) {
      checkConnection(familyInfo.family_id)
      if (isDeviceConnected.value) {
        fetchData()
        connectRealtime(familyInfo.family_id)
      }
    }
  }
})

onPullDownRefresh(async () => {
  await fetchData()
  uni.stopPullDownRefresh()
})
</script>

<style lang="scss" scoped>
@use '@/styles/responsive.scss' as *;
@use '@/styles/variables.scss' as *;

.page {
  min-height: 100vh;
  background: $bg-color-primary;
}

.sidebar-spacer { width: $sidebar-width; }
@include desktop-lg { .sidebar-spacer { width: $sidebar-width-lg; } }
@include desktop-xl { .sidebar-spacer { width: $sidebar-width-xl; } }

.page-content {
  padding: $mobile-pad-y $mobile-pad-x;
  padding-bottom: 140rpx;
  min-height: 100vh;
  box-sizing: border-box;

  &.desktop-content {
    min-height: 100vh;
    padding: 32px 40px;
    max-width: $content-max-width;
    margin: 0 auto;
  }
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-lg;
  padding-top: var(--status-bar-height, 0);
}

@include desktop {
  .page-header {
    margin-bottom: 28px;
    padding-top: 0;
  }
}

.header-title {
  font-size: $font-size-title;
  font-weight: bold;
  color: $text-color-primary;
}

@include desktop {
  .header-title { font-size: 26px; }
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

@include desktop {
  .header-status { gap: 8px; }
}

.status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #94a3b8;
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 8rpx rgba(34, 197, 94, 0.6);
}

@include desktop {
  .status-dot {
    width: 10px;
    height: 10px;
  }
}

.status-text {
  font-size: $font-size-small;
  color: $text-color-secondary;
}

@include desktop {
  .status-text { font-size: 13px; }
}

/* 快捷模式区域 */
.mode-section {
  background: $card-bg-color;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

@include desktop {
  .mode-section {
    padding: 20px 24px;
    border-radius: 16px;
    margin-bottom: 20px;
  }
}

.mode-section-title {
  font-size: $font-size-medium;
  font-weight: bold;
  color: $text-color-secondary;
}

.mode-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

@include desktop {
  .mode-section-header {
    margin-bottom: 14px;
  }
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 4rpx;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.25);
  transition: all 0.3s;

  &:active {
    transform: scale(0.95);
    background: rgba(239, 68, 68, 0.2);
  }

  &.loading {
    opacity: 0.6;
    pointer-events: none;
  }
}

@include desktop {
  .reset-btn {
    padding: 6px 16px;
    border-radius: 16px;
    gap: 4px;

    &:hover {
      background: rgba(239, 68, 68, 0.2);
    }
  }
}

.reset-btn-icon {
  font-size: 28rpx;
}

@include desktop {
  .reset-btn-icon { font-size: 18px; }
}

.reset-btn-text {
  font-size: $font-size-small;
  color: #f87171;
}

@include desktop {
  .reset-btn-text { font-size: 13px; }
}

@include desktop {
  .mode-section-title {
    font-size: 15px;
    margin-bottom: 14px;
  }
}

.mode-buttons {
  display: flex;
  gap: $spacing-md;
}

@include desktop {
  .mode-buttons {
    gap: 16px;
  }
}

.mode-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  padding: $spacing-md;
  border-radius: $border-radius-lg;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.3s;
  cursor: pointer;

  &:active {
    transform: scale(0.96);
  }

  &.loading {
    opacity: 0.6;
    pointer-events: none;
  }
}

@include desktop {
  .mode-btn {
    padding: 18px 20px;
    border-radius: 14px;
    gap: 8px;

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }
  }
}

.mode-btn.morning-mode {
  background: linear-gradient(135deg, #207927, #a3e4a5);
  border-color: #4caf50;
}

.read-mode {
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.12), rgba(249, 115, 22, 0.12));
  border-color: rgba(234, 179, 8, 0.25);
}

.mode-btn-icon {
  font-size: 48rpx;
}

@include desktop {
  .mode-btn-icon {
    font-size: 32px;
  }
}

.mode-btn-name {
  font-size: $font-size-medium;
  font-weight: bold;
  color: $text-color-primary;
}

@include desktop {
  .mode-btn-name {
    font-size: 15px;
  }
}

.mode-btn-desc {
  font-size: $font-size-xs;
  color: $text-color-disabled;
}

@include desktop {
  .mode-btn-desc {
    font-size: 12px;
  }
}

.refresh-tip {
  text-align: center;
  margin-bottom: $spacing-md;
}

.refresh-text {
  font-size: $font-size-small;
  color: $primary-color;
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
}

@include desktop {
  .sensor-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
  }
}

@include desktop-lg {
  .sensor-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
  }
}

@include desktop-xl {
  .sensor-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 22px;
  }
}

.sensor-card {
  background: $card-bg-color;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.3s;

  &:active {
    transform: scale(0.98);
  }
}

@include desktop {
  .sensor-card {
    padding: 22px 20px;
    border-radius: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;

    &:hover {
      background: rgba(255, 255, 255, 0.06);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }
  }
}

.card-icon {
  font-size: 56rpx;
  flex-shrink: 0;
}

@include desktop {
  .card-icon {
    font-size: 36px;
  }
}

.card-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  min-width: 0;
}

@include desktop {
  .card-info {
    gap: 6px;
  }
}

.card-value {
  font-size: $font-size-large;
  font-weight: bold;
  color: $text-color-primary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@include desktop {
  .card-value {
    font-size: 24px;
  }
}

.card-value.placeholder {
  color: $text-color-disabled;
}

.card-value.status-on {
  color: #22c55e;
}

.card-value.status-off {
  color: #94a3b8;
}

.card-unit {
  font-size: $font-size-small;
  color: $text-color-secondary;
  font-weight: normal;
  margin-left: 4rpx;
}

@include desktop {
  .card-unit {
    font-size: 13px;
    margin-left: 4px;
  }
}

.card-label {
  font-size: $font-size-small;
  color: $text-color-secondary;
}

@include desktop {
  .card-label {
    font-size: 13px;
  }
}

/* 特殊卡片样式 */
.temp-card { border-left: 4rpx solid #f97316; }
@include desktop { .temp-card { border-left: none; border-top: 4px solid #f97316; } }

.humi-card { border-left: 4rpx solid #3b82f6; }
@include desktop { .humi-card { border-left: none; border-top: 4px solid #3b82f6; } }

.light-card { border-left: 4rpx solid #eab308; }
@include desktop { .light-card { border-left: none; border-top: 4px solid #eab308; } }

.smoke-card { border-left: 4rpx solid #6b7280; }
.smoke-card.alert { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.1); }
@include desktop {
  .smoke-card { border-left: none; border-top: 4px solid #6b7280; }
  .smoke-card.alert { border-top-color: #ef4444; }
}

.status-card { border-left: 4rpx solid #6b7280; }
.status-card.active { border-left-color: #22c55e; }
@include desktop {
  .status-card { border-left: none; border-top: 4px solid #6b7280; }
  .status-card.active { border-top-color: #22c55e; }
}

.last-update {
  text-align: center;
  margin-top: $spacing-xl;
}

.update-text {
  font-size: $font-size-xs;
  color: $text-color-disabled;
}

@include desktop {
  .update-text { font-size: 12px; }
}

.tabbar-spacer { height: 140rpx; }
</style>
