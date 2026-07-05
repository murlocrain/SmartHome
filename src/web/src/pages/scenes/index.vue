<template>
  <view class="page">
    <view v-if="isDesktop" class="sidebar-spacer"></view>
    <CustomTabBar v-if="isDesktop" :current-index="2" />

    <view class="page-content" :class="{ 'desktop-content': isDesktop }">
      <NetworkGuard v-if="isOffline" :state="'offline'" @retry="retryNetwork" />
      <NetworkGuard v-else-if="authError" :state="'unauthorized'" @retry="retryAuth" />
      <NetworkGuard v-else-if="!isDeviceConnected" :state="connectionState" />

      <template v-else>
        <view class="page-header">
          <text class="header-title">电机控制</text>
          <view class="header-status">
            <view class="status-dot" :class="motorState.onoff ? 'on' : 'off'"></view>
            <text class="status-text">{{ motorState.onoff ? '运行中' : '已停止' }}</text>
          </view>
        </view>

        <!-- 电机可视化预览 -->
        <view class="hero-card" :class="{ 'is-on': motorState.onoff }">
          <view class="motor-preview" :style="{ '--speed': speedRotation }">
            <view class="motor-gear" :class="{ spinning: motorState.onoff }">
              <text class="motor-icon">⚙️</text>
            </view>
            <view class="motor-ring" :class="{ active: motorState.onoff }"></view>
          </view>
          <text class="hero-label">{{ motorState.onoff ? '电机运行中' : '电机已停止' }}</text>
          <text class="hero-speed" v-if="motorState.onoff">{{ motorState.speed }}%</text>

          <!-- 开关按钮 -->
          <view class="switch-row">
            <view
              class="action-btn on-btn"
              :class="{ active: motorState.onoff }"
              @tap="turnMotor('ON')"
            >
              <text class="btn-icon">▶️</text>
              <text class="btn-text">开启</text>
            </view>
            <view
              class="action-btn off-btn"
              :class="{ active: !motorState.onoff }"
              @tap="turnMotor('OFF')"
            >
              <text class="btn-icon">⏹️</text>
              <text class="btn-text">关闭</text>
            </view>
          </view>
        </view>

        <!-- 速度调节 -->
        <view class="control-section">
          <view class="section-head">
            <text class="section-title">调速</text>
            <text class="section-value">{{ motorState.speed }}%</text>
          </view>

          <!-- 速度刻度条 -->
          <view class="speed-bar">
            <view class="speed-fill" :style="{ width: motorState.speed + '%' }"></view>
            <view class="speed-thumb" :style="{ left: motorState.speed + '%' }"></view>
          </view>

          <slider
            class="speed-slider"
            :min="0"
            :max="100"
            :step="1"
            :value="motorState.speed"
            :disabled="!motorState.onoff"
            activeColor="#8b5cf6"
            backgroundColor="rgba(255,255,255,0.1)"
            block-color="#8b5cf6"
            block-size="24"
            @changing="onSpeedChanging"
            @change="onSpeedChange"
          />

          <view class="speed-presets">
            <view
              v-for="p in presets"
              :key="p"
              class="preset-btn"
              :class="{ active: motorState.speed === p }"
              @tap="setSpeed(p)"
            >
              <text>{{ p }}%</text>
            </view>
          </view>
        </view>

        <!-- 快捷控制 -->
        <view class="control-section">
          <text class="section-title">快捷控制</text>
          <view class="quick-row">
            <view class="quick-btn" @tap="setSpeed(0); turnMotor('OFF')">
              <text class="quick-icon">⏸️</text>
              <text class="quick-text">停止</text>
            </view>
            <view class="quick-btn" @tap="setSpeed(30); turnMotor('ON')">
              <text class="quick-icon">🐢</text>
              <text class="quick-text">低速</text>
            </view>
            <view class="quick-btn" @tap="setSpeed(60); turnMotor('ON')">
              <text class="quick-icon">🚶</text>
              <text class="quick-text">中速</text>
            </view>
            <view class="quick-btn" @tap="setSpeed(100); turnMotor('ON')">
              <text class="quick-icon">🚀</text>
              <text class="quick-text">全速</text>
            </view>
          </view>
        </view>
      </template>
    </view>

    <view v-if="!isDesktop" class="tabbar-spacer"></view>
    <CustomTabBar v-if="!isDesktop" :current-index="2" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useNetworkGuard } from '@/composables/useNetwork.js'
import { useDeviceConnection } from '@/composables/useDeviceConnection'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { getRealtimeData, motorOnOff, motorSpeed } from '@/api/device'
import {
  motorState,
  updateMotorState,
  connectRealtime,
  setInitialData,
} from '@/composables/useSensorData'
import CustomTabBar from '@/components/CustomTabBar.vue'
import NetworkGuard from '@/components/NetworkGuard.vue'

const { isOffline, retryNetwork } = useNetworkGuard()
const { isDesktop } = useBreakpoint()
const { connectionState, isDeviceConnected, authError, checkConnection, clearAuthError } = useDeviceConnection()

const presets = [0, 25, 50, 75, 100]

const speedRotation = computed(() => {
  const s = motorState.onoff ? motorState.speed : 0
  return `${2 - s * 0.015}s`
})

async function turnMotor(onoff) {
  const newVal = onoff === 'ON'
  updateMotorState({ onoff })
  try {
    await motorOnOff(onoff)
  } catch (e) {
    updateMotorState({ onoff: newVal ? 'OFF' : 'ON' })
    uni.showToast({ title: '控制失败', icon: 'none' })
  }
}

let speedTimer = null
function onSpeedChanging(e) {
  motorState.speed = e.detail.value
}
function onSpeedChange(e) {
  const val = e.detail.value
  motorState.speed = val
  if (speedTimer) clearTimeout(speedTimer)
  speedTimer = setTimeout(async () => {
    try {
      await motorSpeed(val)
    } catch (err) {
      console.error('调速失败', err)
    }
  }, 150)
}

async function setSpeed(val) {
  if (!motorState.onoff && val > 0) {
    await turnMotor('ON')
  }
  motorState.speed = val
  try {
    await motorSpeed(val)
  } catch (e) {
    uni.showToast({ title: '调速失败', icon: 'none' })
  }
}

async function fetchData() {
  try {
    const familyInfo = uni.getStorageSync('selectedFamily')
    if (!familyInfo) return
    const deviceId = familyInfo.huawei_device_id || familyInfo.device_id
    if (!deviceId) return
    const res = await getRealtimeData(deviceId)
    if (res && res.data) setInitialData(res.data)
  } catch (e) {
    console.error('获取数据失败', e)
  }
}

onMounted(() => {
  fetchData()
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) connectRealtime(familyInfo.family_id)
})

onShow(() => {
  const familyInfo = uni.getStorageSync('selectedFamily')
  if (familyInfo) {
    if (!authError.value) {
      checkConnection(familyInfo.family_id)
      fetchData()
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

.header-status { display: flex; align-items: center; gap: 8rpx; }
@include desktop { .header-status { gap: 8px; } }

.status-dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: #94a3b8; }
.status-dot.on { background: #8b5cf6; box-shadow: 0 0 8rpx rgba(139, 92, 246, 0.7); }
@include desktop { .status-dot { width: 10px; height: 10px; } }

.status-text { font-size: $font-size-small; color: $text-color-secondary; }
@include desktop { .status-text { font-size: 13px; } }

/* ========== Hero 卡片 ========== */
.hero-card {
  background: $card-bg-color;
  border-radius: $border-radius-xl;
  padding: $spacing-xl;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.4s ease;

  &.is-on {
    background: linear-gradient(145deg, rgba(139, 92, 246, 0.08), rgba(30, 41, 59, 0.9));
    border-color: rgba(139, 92, 246, 0.2);
  }
}
@include desktop {
  .hero-card { padding: 36px; border-radius: 20px; gap: 20px; margin-bottom: 24px; }
}

.motor-preview {
  position: relative;
  width: 180rpx;
  height: 180rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
@include desktop { .motor-preview { width: 150px; height: 150px; } }

.motor-gear {
  position: relative;
  z-index: 2;
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(139, 92, 246, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s ease;
}
.motor-gear.spinning {
  background: rgba(139, 92, 246, 0.25);
  animation: spin var(--speed, 1s) linear infinite;
}
@include desktop {
  .motor-gear { width: 100px; height: 100px; }
}

.motor-icon { font-size: 70rpx; }
@include desktop { .motor-icon { font-size: 58px; } }

.motor-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3rpx dashed rgba(139, 92, 246, 0.3);
  z-index: 1;
  animation: spin 4s linear infinite;
  animation-play-state: paused;
}
.motor-ring.active {
  animation-play-state: running;
  animation-duration: var(--speed, 1s);
  border-color: rgba(139, 92, 246, 0.6);
}
@include desktop { .motor-ring { border-width: 3px; } }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.hero-label {
  font-size: $font-size-large;
  color: $text-color-primary;
  font-weight: 500;
}
@include desktop { .hero-label { font-size: 20px; } }

.hero-speed {
  font-size: 60rpx;
  font-weight: bold;
  color: #8b5cf6;
}
@include desktop { .hero-speed { font-size: 48px; } }

/* 开关按钮行 */
.switch-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
  width: 100%;
  margin-top: $spacing-sm;
}
@include desktop { .switch-row { gap: 16px; margin-top: 8px; } }

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-md;
  border-radius: $border-radius-md;
  background: rgba(255,255,255,0.05);
  border: 2rpx solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;

  &.on-btn.active {
    background: rgba(34, 197, 94, 0.15);
    border-color: #22c55e;
  }
  &.off-btn.active {
    background: rgba(239, 68, 68, 0.15);
    border-color: #ef4444;
  }
  &:active { transform: scale(0.97); }
}
@include desktop {
  .action-btn {
    padding: 18px;
    border-radius: 14px;
    border-width: 2px;
    gap: 8px;
    &:hover { background: rgba(255,255,255,0.1); }
  }
}

.btn-icon { font-size: 44rpx; }
@include desktop { .btn-icon { font-size: 32px; } }

.btn-text { font-size: $font-size-small; color: $text-color-primary; font-weight: 500; }
@include desktop { .btn-text { font-size: 14px; } }

/* ========== 控制区块 ========== */
.control-section {
  background: $card-bg-color;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
  border: 1px solid rgba(255,255,255,0.04);
}
@include desktop {
  .control-section { padding: 24px; border-radius: 16px; margin-bottom: 20px; }
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title { font-size: $font-size-medium; color: $text-color-primary; font-weight: 600; margin-bottom: $spacing-md; display: block; }
.section-head .section-title { margin-bottom: 0; }
@include desktop { .section-title { font-size: 16px; margin-bottom: 16px; } }

.section-value { font-size: $font-size-medium; color: #8b5cf6; font-weight: bold; }
@include desktop { .section-value { font-size: 16px; } }

/* 速度可视化条 */
.speed-bar {
  height: 16rpx;
  background: rgba(255,255,255,0.08);
  border-radius: 16rpx;
  position: relative;
  margin-bottom: $spacing-sm;
  overflow: visible;
}
@include desktop { .speed-bar { height: 10px; border-radius: 10px; margin-bottom: 12px; } }

.speed-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
  border-radius: 16rpx;
  transition: width 0.2s ease;
}
@include desktop { .speed-fill { border-radius: 10px; } }

.speed-thumb {
  position: absolute;
  top: 50%;
  width: 28rpx;
  height: 28rpx;
  background: #fff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 2rpx 8rpx rgba(139, 92, 246, 0.5);
  transition: left 0.2s ease;
}
@include desktop { .speed-thumb { width: 18px; height: 18px; } }

.speed-slider { margin: 0; }

/* 预设速度按钮 */
.speed-presets {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: $spacing-xs;
  margin-top: $spacing-sm;
}
@include desktop { .speed-presets { gap: 8px; margin-top: 12px; } }

.preset-btn {
  text-align: center;
  padding: $spacing-sm 0;
  border-radius: $border-radius-sm;
  background: rgba(255,255,255,0.05);
  font-size: $font-size-xs;
  color: $text-color-secondary;
  transition: all 0.2s ease;
  cursor: pointer;

  &.active {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    font-weight: bold;
  }
}
@include desktop {
  .preset-btn {
    padding: 10px 0;
    border-radius: 8px;
    font-size: 13px;
    &:hover { background: rgba(255,255,255,0.1); }
  }
}

/* 快捷控制 */
.quick-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-sm;
}
@include desktop { .quick-row { gap: 12px; } }

.quick-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-xs;
  padding: $spacing-md $spacing-sm;
  border-radius: $border-radius-md;
  background: rgba(255,255,255,0.04);
  transition: all 0.2s ease;
  cursor: pointer;

  &:active { transform: scale(0.95); background: rgba(139, 92, 246, 0.1); }
}
@include desktop {
  .quick-btn {
    padding: 18px 8px;
    border-radius: 12px;
    gap: 8px;
    &:hover { background: rgba(139, 92, 246, 0.12); }
  }
}

.quick-icon { font-size: 40rpx; }
@include desktop { .quick-icon { font-size: 28px; } }

.quick-text { font-size: $font-size-xs; color: $text-color-secondary; }
@include desktop { .quick-text { font-size: 12px; } }

.tabbar-spacer { height: 140rpx; }
</style>
