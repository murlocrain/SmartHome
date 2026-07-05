<template>
  <view class="page">
    <view v-if="isDesktop" class="sidebar-spacer"></view>
    <CustomTabBar v-if="isDesktop" :current-index="3" />

    <view class="page-content" :class="{ 'desktop-content': isDesktop }">
      <NetworkGuard v-if="isOffline" :state="'offline'" @retry="retryNetwork" />
      <NetworkGuard v-else-if="authError" :state="'unauthorized'" @retry="retryAuth" />
      <NetworkGuard v-else-if="!isDeviceConnected" :state="connectionState" />

      <template v-else>
        <view class="page-header">
          <text class="header-title">设备状态</text>
          <view class="refresh-btn" @tap="refreshAll">
            <text class="refresh-icon">🔄</text>
          </view>
        </view>

        <!-- 在线状态大卡片 -->
        <view class="hero-card" :class="sysStatus.online ? 'online' : 'offline'">
          <view class="hero-icon-wrap">
            <text class="hero-icon">{{ sysStatus.online ? '🟢' : '🔴' }}</text>
          </view>
          <text class="hero-status">{{ sysStatus.online ? '设备在线' : '设备离线' }}</text>
          <text class="hero-sub" v-if="sysStatus.last_seen">最后通信: {{ formatTime(sysStatus.last_seen) }}</text>
        </view>

        <!-- 连接状态列表 -->
        <view class="status-section">
          <text class="section-title">连接状态</text>

          <view class="status-list">
            <view class="status-row">
              <view class="status-left">
                <text class="status-icon">📶</text>
                <text class="status-name">WiFi</text>
              </view>
              <view class="status-right">
                <view class="status-badge" :class="sysStatus.wifi ? 'ok' : 'bad'">
                  <text>{{ sysStatus.wifi ? '已连接' : '未连接' }}</text>
                </view>
                <text class="status-detail" v-if="sysStatus.wifi_rssi">{{ sysStatus.wifi_rssi }} dBm</text>
              </view>
            </view>

            <view class="status-row">
              <view class="status-left">
                <text class="status-icon">☁️</text>
                <text class="status-name">MQTT</text>
              </view>
              <view class="status-badge" :class="sysStatus.mqtt ? 'ok' : 'bad'">
                <text>{{ sysStatus.mqtt ? '已连接' : '未连接' }}</text>
              </view>
            </view>

            <view class="status-row">
              <view class="status-left">
                <text class="status-icon">🌐</text>
                <text class="status-name">设备在线</text>
              </view>
              <view class="status-badge" :class="sysStatus.online ? 'ok' : 'bad'">
                <text>{{ sysStatus.online ? '在线' : '离线' }}</text>
              </view>
            </view>

            <view class="status-row" v-if="sysStatus.ip !== null && sysStatus.ip !== undefined">
              <view class="status-left">
                <text class="status-icon">🏷️</text>
                <text class="status-name">IP地址</text>
              </view>
              <text class="status-ip">{{ sysStatus.ip }}</text>
            </view>
          </view>
        </view>

        <!-- 蜂鸣器控制 -->
        <view class="control-section">
          <text class="section-title">蜂鸣器</text>
          <view class="buzzer-card">
            <view class="buzzer-icon-wrap">
              <text class="buzzer-icon">🔔</text>
            </view>
            <view class="buzzer-info">
              <text class="buzzer-label">播放提示音</text>
              <text class="buzzer-desc">频率 {{ beepState.frequency }}Hz · {{ beepState.duration }}ms</text>
            </view>
            <view class="buzzer-btn" :class="{ playing: beepPlaying }" @tap="playBeep">
              <text>{{ beepPlaying ? '播放中...' : '播放' }}</text>
            </view>
          </view>

          <!-- 频率调节 -->
          <view class="sub-control">
            <view class="sub-head">
              <text class="sub-label">频率 (Hz)</text>
              <text class="sub-value">{{ beepState.frequency }}</text>
            </view>
            <slider
              :min="500"
              :max="4000"
              :step="100"
              :value="beepState.frequency"
              activeColor="#f59e0b"
              backgroundColor="rgba(255,255,255,0.1)"
              block-color="#f59e0b"
              @change="e => beepState.frequency = e.detail.value"
            />
          </view>

          <!-- 持续时间 -->
          <view class="sub-control">
            <view class="sub-head">
              <text class="sub-label">持续时间 (ms)</text>
              <text class="sub-value">{{ beepState.duration }}</text>
            </view>
            <slider
              :min="100"
              :max="3000"
              :step="100"
              :value="beepState.duration"
              activeColor="#f59e0b"
              backgroundColor="rgba(255,255,255,0.1)"
              block-color="#f59e0b"
              @change="e => beepState.duration = e.detail.value"
            />
          </view>
        </view>

        <!-- 语音命令状态 -->
        <view class="control-section">
          <text class="section-title">语音控制</text>
          <view class="voice-card">
            <view class="voice-icon-wrap">
              <text class="voice-icon">🎤</text>
            </view>
            <view class="voice-info">
              <text class="voice-label">最近命令</text>
              <view class="voice-result" v-if="voiceText">
                <text class="voice-cmd">{{ voiceText }}</text>
                <view class="voice-badge ok">
                  <text>识别成功</text>
                </view>
              </view>
              <text class="voice-empty" v-else>暂无语音命令</text>
            </view>
          </view>
        </view>
      </template>
    </view>

    <view v-if="!isDesktop" class="tabbar-spacer"></view>
    <CustomTabBar v-if="!isDesktop" :current-index="3" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useNetworkGuard } from '@/composables/useNetwork.js'
import { useDeviceConnection } from '@/composables/useDeviceConnection'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { getRealtimeData, getSystemStatus, beepPlay } from '@/api/device'
import {
  sensorData,
  beepState,
  connectRealtime,
  setInitialData,
} from '@/composables/useSensorData'
import CustomTabBar from '@/components/CustomTabBar.vue'
import NetworkGuard from '@/components/NetworkGuard.vue'

const { isOffline, retryNetwork } = useNetworkGuard()
const { isDesktop } = useBreakpoint()
const { connectionState, isDeviceConnected, authError, checkConnection, clearAuthError } = useDeviceConnection()

const sysStatus = ref({
  online: false,
  wifi: false,
  wifi_rssi: null,
  ip: null,
  mqtt: false,
  ws_clients: 0,
  last_seen: null,
  huawei_enabled: false,
})

const beepPlaying = ref(false)

const voiceText = computed(() => {
  const raw = sensorData.voice_command
  if (!raw) return ''
  // 简单的命令解析映射
  const cmd = String(raw).trim().toUpperCase()
  const map = {
    '01': '开灯', 'ON': '开灯', 'KAIDENG': '开灯',
    '02': '关灯', 'OFF': '关灯', 'GUANDENG': '关灯',
    '03': '红色', 'RED': '红色', 'HONGSE': '红色',
    '04': '绿色', 'GREEN': '绿色', 'LVSE': '绿色',
    '05': '蓝色', 'BLUE': '蓝色', 'LANSE': '蓝色',
    '06': '电机开', 'MOTORON': '电机开启',
    '07': '电机关', 'MOTOROFF': '电机关闭',
    '08': '播放提示音', 'BEEP': '播放提示音',
  }
  if (map[cmd]) return map[cmd]
  // 尝试匹配中文原文
  if (/[\u4e00-\u9fa5]/.test(raw)) return raw
  return raw
})

function formatTime(isoStr) {
  if (!isoStr) return '--'
  try {
    const d = new Date(isoStr)
    const now = new Date()
    const diff = (now - d) / 1000
    if (diff < 60) return `${Math.floor(diff)}秒前`
    if (diff < 3600) return `${Math.floor(diff/60)}分钟前`
    return `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}`
  } catch { return isoStr }
}

async function refreshAll() {
  await Promise.all([fetchSensorData(), fetchSysStatus()])
  uni.showToast({ title: '已刷新', icon: 'none', duration: 800 })
}

async function fetchSensorData() {
  try {
    const familyInfo = uni.getStorageSync('selectedFamily')
    if (!familyInfo) return
    const deviceId = familyInfo.huawei_device_id || familyInfo.device_id
    if (!deviceId) return
    const res = await getRealtimeData(deviceId)
    if (res && res.data) setInitialData(res.data)
    if (res && res.online !== undefined) sysStatus.value.online = res.online
  } catch (e) {
    console.error('获取传感器数据失败', e)
  }
}

async function fetchSysStatus() {
  try {
    const familyInfo = uni.getStorageSync('selectedFamily')
    if (!familyInfo) return
    const deviceId = familyInfo.huawei_device_id || familyInfo.device_id
    if (!deviceId) return
    const res = await getSystemStatus(deviceId)
    if (res) Object.assign(sysStatus.value, res)
  } catch (e) {
    console.error('获取系统状态失败', e)
  }
}

async function playBeep() {
  if (beepPlaying.value) return
  beepPlaying.value = true
  try {
    await beepPlay(beepState.duration, beepState.frequency)
    setTimeout(() => { beepPlaying.value = false }, beepState.duration)
  } catch (e) {
    beepPlaying.value = false
    uni.showToast({ title: '播放失败', icon: 'none' })
  }
}

onMounted(() => {
  refreshAll()
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) connectRealtime(familyInfo.family_id)
})

onShow(() => {
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) {
    if (!authError.value) {
      checkConnection(familyInfo.family_id)
      refreshAll()
      connectRealtime(familyInfo.family_id)
    }
  }
})

function retryAuth() {
  clearAuthError()
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) {
    checkConnection(familyInfo.family_id)
  }
}
</script>

<style lang="scss" scoped>
@use '@/styles/responsive.scss' as *;
@use '@/styles/variables.scss' as *;

.page { min-height: 100vh; background: $bg-color-primary; }

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
@include desktop { .page-header { margin-bottom: 28px; padding-top: 0; } }

.header-title { font-size: $font-size-title; font-weight: bold; color: $text-color-primary; }
@include desktop { .header-title { font-size: 26px; } }

.refresh-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}
.refresh-icon { font-size: 32rpx; }
@include desktop {
  .refresh-btn { width: 40px; height: 40px; }
  .refresh-icon { font-size: 20px; }
}

/* ========== Hero 在线状态卡片 ========== */
.hero-card {
  border-radius: $border-radius-xl;
  padding: $spacing-xl;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  margin-bottom: $spacing-lg;
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.3s ease;

  &.online {
    background: linear-gradient(145deg, rgba(34, 197, 94, 0.12), rgba(30, 41, 59, 0.9));
    border-color: rgba(34, 197, 94, 0.3);
  }
  &.offline {
    background: linear-gradient(145deg, rgba(239, 68, 68, 0.1), rgba(30, 41, 59, 0.9));
    border-color: rgba(239, 68, 68, 0.25);
  }
}
@include desktop {
  .hero-card {
    padding: 36px;
    border-radius: 20px;
    gap: 12px;
    margin-bottom: 24px;
  }
}

.hero-icon-wrap {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.06);
}
@include desktop { .hero-icon-wrap { width: 90px; height: 90px; } }

.hero-icon { font-size: 60rpx; }
@include desktop { .hero-icon { font-size: 44px; } }

.hero-status {
  font-size: $font-size-xl;
  font-weight: bold;
  color: $text-color-primary;
}
@include desktop { .hero-status { font-size: 24px; } }

.hero-sub {
  font-size: $font-size-xs;
  color: $text-color-disabled;
}
@include desktop { .hero-sub { font-size: 12px; } }

/* ========== 区块通用 ========== */
.control-section,
.status-section {
  background: $card-bg-color;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
  border: 1px solid rgba(255,255,255,0.04);
}
@include desktop {
  .control-section, .status-section {
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 20px;
  }
}

.section-title {
  font-size: $font-size-medium;
  color: $text-color-primary;
  font-weight: 600;
  margin-bottom: $spacing-md;
  display: block;
}
@include desktop { .section-title { font-size: 16px; margin-bottom: 18px; } }

/* ========== 状态列表 ========== */
.status-list { display: flex; flex-direction: column; }

.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-md 0;
  border-bottom: 1rpx solid rgba(255,255,255,0.04);

  &:last-child { border-bottom: none; }
}
@include desktop {
  .status-row { padding: 16px 0; }
}

.status-left { display: flex; align-items: center; gap: $spacing-md; }
@include desktop { .status-left { gap: 14px; } }

.status-icon { font-size: 40rpx; }
@include desktop { .status-icon { font-size: 24px; } }

.status-name { font-size: $font-size-medium; color: $text-color-primary; }
@include desktop { .status-name { font-size: 15px; } }

.status-right { display: flex; align-items: center; gap: $spacing-sm; }
@include desktop { .status-right { gap: 10px; } }

.status-badge {
  padding: 6rpx 18rpx;
  border-radius: 20rpx;
  font-size: $font-size-xs;

  &.ok {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
    border: 1rpx solid rgba(34, 197, 94, 0.3);
  }
  &.bad {
    background: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1rpx solid rgba(239, 68, 68, 0.3);
  }
}
@include desktop {
  .status-badge {
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    border-width: 1px;
  }
}

.status-detail {
  font-size: $font-size-xs;
  color: $text-color-secondary;
}
@include desktop { .status-detail { font-size: 12px; } }

.status-ip {
  font-size: $font-size-small;
  color: $text-color-secondary;
  font-family: monospace;
}
@include desktop { .status-ip { font-size: 13px; } }

/* ========== 蜂鸣器 ========== */
.buzzer-card {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md;
  background: rgba(245, 158, 11, 0.06);
  border-radius: $border-radius-md;
  border: 1rpx solid rgba(245, 158, 11, 0.15);
  margin-bottom: $spacing-md;
}
@include desktop {
  .buzzer-card { padding: 18px; border-radius: 14px; gap: 16px; margin-bottom: 18px; }
}

.buzzer-icon-wrap {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: rgba(245, 158, 11, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
@include desktop { .buzzer-icon-wrap { width: 60px; height: 60px; } }

.buzzer-icon { font-size: 48rpx; }
@include desktop { .buzzer-icon { font-size: 32px; } }

.buzzer-info { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
@include desktop { .buzzer-info { gap: 4px; } }

.buzzer-label { font-size: $font-size-medium; color: $text-color-primary; font-weight: 500; }
@include desktop { .buzzer-label { font-size: 15px; } }

.buzzer-desc { font-size: $font-size-xs; color: $text-color-secondary; }
@include desktop { .buzzer-desc { font-size: 12px; } }

.buzzer-btn {
  padding: $spacing-sm $spacing-lg;
  border-radius: $border-radius-md;
  background: #f59e0b;
  color: #fff;
  font-size: $font-size-small;
  font-weight: 600;
  transition: all 0.2s ease;

  &:active { transform: scale(0.95); }
  &.playing {
    background: #6b7280;
    pointer-events: none;
  }
}
@include desktop {
  .buzzer-btn {
    padding: 10px 22px;
    border-radius: 10px;
    font-size: 14px;
    cursor: pointer;
    &:hover { background: #d97706; }
  }
}

.sub-control { margin-bottom: $spacing-md; }
.sub-control:last-child { margin-bottom: 0; }
@include desktop { .sub-control { margin-bottom: 14px; } }

.sub-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-xs;
}
.sub-label { font-size: $font-size-small; color: $text-color-secondary; }
.sub-value { font-size: $font-size-small; color: #f59e0b; font-weight: 600; }
@include desktop {
  .sub-label { font-size: 13px; }
  .sub-value { font-size: 13px; }
}

/* ========== 语音命令 ========== */
.voice-card {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  padding: $spacing-md;
  background: rgba(129, 140, 248, 0.06);
  border-radius: $border-radius-md;
  border: 1rpx solid rgba(129, 140, 248, 0.15);
}
@include desktop {
  .voice-card { padding: 18px; border-radius: 14px; gap: 16px; }
}

.voice-icon-wrap {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: rgba(129, 140, 248, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
@include desktop { .voice-icon-wrap { width: 60px; height: 60px; } }

.voice-icon { font-size: 48rpx; }
@include desktop { .voice-icon { font-size: 32px; } }

.voice-info { flex: 1; display: flex; flex-direction: column; gap: 8rpx; min-width: 0; }
@include desktop { .voice-info { gap: 8px; } }

.voice-label { font-size: $font-size-small; color: $text-color-secondary; }
@include desktop { .voice-label { font-size: 13px; } }

.voice-result { display: flex; align-items: center; gap: $spacing-sm; flex-wrap: wrap; }
@include desktop { .voice-result { gap: 10px; } }

.voice-cmd {
  font-size: $font-size-large;
  color: #818cf8;
  font-weight: bold;
}
@include desktop { .voice-cmd { font-size: 20px; } }

.voice-badge {
  padding: 4rpx 14rpx;
  border-radius: 16rpx;
  font-size: $font-size-xs;

  &.ok {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
  }
}
@include desktop {
  .voice-badge { padding: 3px 10px; border-radius: 12px; font-size: 11px; }
}

.voice-empty { font-size: $font-size-small; color: $text-color-disabled; }
@include desktop { .voice-empty { font-size: 13px; } }

.tabbar-spacer { height: 140rpx; }
</style>
