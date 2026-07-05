<template>
  <view class="page">
    <view v-if="isDesktop" class="sidebar-spacer"></view>
    <CustomTabBar v-if="isDesktop" :current-index="1" />

    <view class="page-content" :class="{ 'desktop-content': isDesktop }">
      <NetworkGuard v-if="isOffline" :state="'offline'" @retry="retryNetwork" />
      <NetworkGuard v-else-if="authError" :state="'unauthorized'" @retry="retryAuth" />
      <NetworkGuard v-else-if="!isDeviceConnected" :state="connectionState" />

      <template v-else>
        <view class="page-header">
          <text class="header-title">灯光控制</text>
          <view class="header-status">
            <view class="status-dot" :class="lightState.onoff ? 'on' : 'off'"></view>
            <text class="status-text">{{ lightState.onoff ? '开启中' : '已关闭' }}</text>
          </view>
        </view>

        <!-- 大开关 -->
        <view class="hero-card" :class="{ 'is-on': lightState.onoff }">
          <view class="hero-light-preview" :style="lightPreviewStyle">
            <text class="hero-icon">💡</text>
          </view>
          <text class="hero-label">{{ lightState.onoff ? '灯光已开启' : '灯光已关闭' }}</text>
          <view class="switch-wrap">
            <view
              class="big-switch"
              :class="{ active: lightState.onoff }"
              @tap="toggleLight"
            >
              <view class="switch-thumb"></view>
            </view>
          </view>
        </view>

        <!-- 颜色选择 -->
        <view class="control-section">
          <text class="section-title">颜色切换</text>
          <view class="color-grid">
            <view
              v-for="c in colors"
              :key="c.key"
              class="color-btn"
              :class="{ active: lightState.color === c.key, 'is-off': !lightState.onoff }"
              :style="{ background: c.css }"
              @tap="selectColor(c.key)"
            >
              <view v-if="lightState.color === c.key" class="color-check">✓</view>
              <text class="color-label">{{ c.name }}</text>
            </view>
          </view>
        </view>

        <!-- 亮度调节 -->
        <view class="control-section">
          <view class="section-head">
            <text class="section-title">亮度调节</text>
            <text class="section-value">{{ brightnessPercent }}%</text>
          </view>
          <slider
            class="brightness-slider"
            :min="0"
            :max="255"
            :step="1"
            :value="lightState.brightness"
            :disabled="!lightState.onoff"
            activeColor="#fbbf24"
            backgroundColor="rgba(255,255,255,0.1)"
            block-color="#fbbf24"
            block-size="24"
            @changing="onBrightnessChanging"
            @change="onBrightnessChange"
          />
          <view class="slider-labels">
            <text class="slider-label">0</text>
            <text class="slider-label">255</text>
          </view>
        </view>

        <!-- 模式切换 -->
        <view class="control-section">
          <text class="section-title">灯光模式</text>
          <view class="mode-row">
            <view
              class="mode-btn"
              :class="{ active: lightState.mode === 'STATIC', 'is-off': !lightState.onoff }"
              @tap="setMode('STATIC')"
            >
              <text class="mode-icon">☀️</text>
              <text class="mode-name">常亮</text>
            </view>
            <view
              class="mode-btn"
              :class="{ active: lightState.mode === 'BREATH', 'is-off': !lightState.onoff }"
              @tap="setMode('BREATH')"
            >
              <text class="mode-icon">🌊</text>
              <text class="mode-name">呼吸灯</text>
            </view>
          </view>
        </view>
      </template>
    </view>

    <view v-if="!isDesktop" class="tabbar-spacer"></view>
    <CustomTabBar v-if="!isDesktop" :current-index="1" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useNetworkGuard } from '@/composables/useNetwork.js'
import { useDeviceConnection } from '@/composables/useDeviceConnection'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { getRealtimeData, lightOnOff, lightColor, lightBrightness, lightMode } from '@/api/device'
import {
  sensorData,
  lightState,
  updateLightState,
  connectRealtime,
  setInitialData,
} from '@/composables/useSensorData'
import CustomTabBar from '@/components/CustomTabBar.vue'
import NetworkGuard from '@/components/NetworkGuard.vue'

const { isOffline, retryNetwork } = useNetworkGuard()
const { isDesktop } = useBreakpoint()
const { connectionState, isDeviceConnected, authError, checkConnection, clearAuthError } = useDeviceConnection()

const brightnessPercent = computed(() => Math.round((lightState.brightness / 255) * 100))

const colors = [
  { key: 'WHITE',  name: '白色', css: '#ffffff' },
  { key: 'RED',    name: '红色', css: '#ef4444' },
  { key: 'GREEN',  name: '绿色', css: '#22c55e' },
  { key: 'BLUE',   name: '蓝色', css: '#3b82f6' },
  { key: 'YELLOW', name: '黄色', css: '#eab308' },
  { key: 'CYAN',   name: '青色', css: '#06b6d4' },
  { key: 'PURPLE', name: '紫色', css: '#a855f7' },
]

const colorMap = {
  WHITE:  '#ffffff',
  RED:    '#ef4444',
  GREEN:  '#22c55e',
  BLUE:   '#3b82f6',
  YELLOW: '#eab308',
  CYAN:   '#06b6d4',
  PURPLE: '#a855f7',
}

const lightPreviewStyle = computed(() => {
  const on = lightState.onoff
  const color = colorMap[lightState.color] || '#ffffff'
  const brightness = lightState.brightness / 255
  const intensity = on ? (0.3 + brightness * 0.7) : 0.05
  return {
    background: on ? color : '#1f2937',
    boxShadow: on
      ? `0 0 ${Math.round(40 * intensity)}px ${color}, 0 0 ${Math.round(80 * intensity)}px ${color}40`
      : 'none',
    opacity: on ? (0.6 + brightness * 0.4) : 0.3,
  }
})

async function toggleLight() {
  const newVal = !lightState.onoff
  updateLightState({ onoff: newVal ? 'ON' : 'OFF' })
  try {
    await lightOnOff(newVal ? 'ON' : 'OFF')
  } catch (e) {
    console.error('灯光控制失败', e)
    updateLightState({ onoff: newVal ? 'OFF' : 'ON' })
    uni.showToast({ title: '控制失败', icon: 'none' })
  }
}

async function selectColor(key) {
  if (!lightState.onoff) return
  if (lightState.color === key) return
  const old = lightState.color
  updateLightState({ color: key })
  try {
    await lightColor(key)
  } catch (e) {
    updateLightState({ color: old })
    uni.showToast({ title: '设置失败', icon: 'none' })
  }
}

let brightnessTimer = null
function onBrightnessChanging(e) {
  lightState.brightness = e.detail.value
}
function onBrightnessChange(e) {
  const val = e.detail.value
  lightState.brightness = val
  if (brightnessTimer) clearTimeout(brightnessTimer)
  brightnessTimer = setTimeout(async () => {
    try {
      await lightBrightness(val)
    } catch (err) {
      console.error('亮度调节失败', err)
    }
  }, 150)
}

async function setMode(mode) {
  if (!lightState.onoff) return
  if (lightState.mode === mode) return
  const old = lightState.mode
  updateLightState({ mode })
  try {
    await lightMode(mode)
  } catch (e) {
    updateLightState({ mode: old })
    uni.showToast({ title: '设置失败', icon: 'none' })
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

.header-title {
  font-size: $font-size-title;
  font-weight: bold;
  color: $text-color-primary;
}
@include desktop { .header-title { font-size: 26px; } }

.header-status {
  display: flex;
  align-items: center;
  gap: 8rpx;
}
@include desktop { .header-status { gap: 8px; } }

.status-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: #94a3b8;
}
.status-dot.on { background: #fbbf24; box-shadow: 0 0 8rpx rgba(251, 191, 36, 0.7); }
@include desktop { .status-dot { width: 10px; height: 10px; } }

.status-text { font-size: $font-size-small; color: $text-color-secondary; }
@include desktop { .status-text { font-size: 13px; } }

/* ========== Hero 大卡片 ========== */
.hero-card {
  background: $card-bg-color;
  border-radius: $border-radius-xl;
  padding: $spacing-xl;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: all 0.4s ease;

  &.is-on {
    background: linear-gradient(145deg, rgba(251, 191, 36, 0.08), rgba(30, 41, 59, 0.9));
    border-color: rgba(251, 191, 36, 0.2);
  }
}

@include desktop {
  .hero-card {
    padding: 36px;
    border-radius: 20px;
    gap: 24px;
    margin-bottom: 24px;
  }
}

.hero-light-preview {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s ease;
}

@include desktop {
  .hero-light-preview {
    width: 140px;
    height: 140px;
  }
}

.hero-icon {
  font-size: 80rpx;
  filter: drop-shadow(0 0 20rpx rgba(255,255,255,0.3));
}
@include desktop { .hero-icon { font-size: 70px; } }

.hero-label {
  font-size: $font-size-large;
  color: $text-color-primary;
  font-weight: 500;
}
@include desktop { .hero-label { font-size: 20px; } }

.switch-wrap { display: flex; align-items: center; justify-content: center; }

.big-switch {
  width: 100rpx;
  height: 56rpx;
  border-radius: 56rpx;
  background: rgba(255,255,255,0.1);
  position: relative;
  transition: all 0.3s ease;
}
.big-switch.active { background: #fbbf24; }

.switch-thumb {
  position: absolute;
  top: 6rpx;
  left: 6rpx;
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #fff;
  transition: all 0.3s ease;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.3);
}
.big-switch.active .switch-thumb {
  left: 50rpx;
}

@include desktop {
  .big-switch { width: 64px; height: 36px; border-radius: 36px; }
  .switch-thumb { top: 4px; left: 4px; width: 28px; height: 28px; }
  .big-switch.active .switch-thumb { left: 32px; }
}

/* ========== 控制区块 ========== */
.control-section {
  background: $card-bg-color;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  margin-bottom: $spacing-md;
  border: 1px solid rgba(255, 255, 255, 0.04);
}
@include desktop {
  .control-section {
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 20px;
  }
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-md;
}

.section-title {
  font-size: $font-size-medium;
  color: $text-color-primary;
  font-weight: 600;
  margin-bottom: $spacing-md;
  display: block;
}
.section-head .section-title { margin-bottom: 0; }
@include desktop { .section-title { font-size: 16px; margin-bottom: 16px; } }

.section-value {
  font-size: $font-size-medium;
  color: #fbbf24;
  font-weight: bold;
}
@include desktop { .section-value { font-size: 16px; } }

/* 颜色按钮 */
.color-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $spacing-sm;
}
@include desktop {
  .color-grid {
    grid-template-columns: repeat(7, 1fr);
    gap: 12px;
  }
}

.color-btn {
  aspect-ratio: 1;
  border-radius: $border-radius-md;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  border: 3rpx solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;

  &.active {
    border-color: #fff;
    transform: scale(1.05);
    box-shadow: 0 4rpx 16rpx rgba(255,255,255,0.2);
  }
  &.is-off {
    opacity: 0.4;
    pointer-events: none;
  }
}

@include desktop {
  .color-btn {
    aspect-ratio: 1;
    border-radius: 14px;
    border-width: 3px;
    &:hover { transform: scale(1.08); }
  }
}

.color-check {
  position: absolute;
  top: 6rpx;
  right: 6rpx;
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
@include desktop {
  .color-check {
    top: 6px;
    right: 6px;
    width: 22px;
    height: 22px;
    font-size: 13px;
  }
}

.color-label {
  font-size: $font-size-xs;
  color: #fff;
  text-shadow: 0 1rpx 3rpx rgba(0,0,0,0.7);
  margin-top: 4rpx;
}
@include desktop { .color-label { font-size: 11px; } }

/* 亮度滑杆 */
.brightness-slider {
  margin: $spacing-sm 0 $spacing-xs;
}
@include desktop { .brightness-slider { margin: 16px 0 8px; } }

.slider-labels {
  display: flex;
  justify-content: space-between;
}
.slider-label {
  font-size: $font-size-xs;
  color: $text-color-disabled;
}
@include desktop { .slider-label { font-size: 12px; } }

/* 模式 */
.mode-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-md;
}
@include desktop { .mode-row { gap: 16px; } }

.mode-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-lg;
  border-radius: $border-radius-md;
  background: rgba(255,255,255,0.04);
  border: 2rpx solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;

  &.active {
    background: rgba(251, 191, 36, 0.12);
    border-color: #fbbf24;
  }
  &.is-off {
    opacity: 0.4;
    pointer-events: none;
  }
}
@include desktop {
  .mode-btn {
    padding: 24px;
    border-radius: 14px;
    border-width: 2px;
    gap: 10px;
    &:hover { background: rgba(255,255,255,0.08); }
  }
}

.mode-icon { font-size: 48rpx; }
@include desktop { .mode-icon { font-size: 36px; } }

.mode-name { font-size: $font-size-small; color: $text-color-primary; }
@include desktop { .mode-name { font-size: 14px; } }

.tabbar-spacer { height: 140rpx; }
</style>
