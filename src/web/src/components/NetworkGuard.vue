<template>
  <view class="placeholder-root" :style="{ background: theme.bgColor }">
    <view class="placeholder-nav" :style="{ background: theme.cardColor }">
      <text class="placeholder-nav-title" :style="{ color: theme.textColor }">智能家居</text>
    </view>

    <!-- 认证失败 -->
    <view class="placeholder-body" v-if="state === 'unauthorized'">
      <view class="placeholder-card" :style="{ background: theme.cardColor }">
        <view class="placeholder-icon-wrap">
          <text class="placeholder-icon">🔒</text>
        </view>
        <text class="placeholder-title" :style="{ color: theme.textColor }">登录已过期</text>
        <text class="placeholder-desc" :style="{ color: theme.textSecondary }">您的登录凭证已失效，请重新登录</text>
        <view class="placeholder-retry" :style="{ background: theme.primaryColor }" @tap="goLogin">
          <text class="retry-text" :style="{ color: '#fff' }">去登录</text>
        </view>
      </view>
    </view>

    <!-- 网络离线状态 -->
    <view class="placeholder-body" v-else-if="state === 'offline'">
      <view class="placeholder-card" :style="{ background: theme.cardColor }">
        <view class="placeholder-icon-wrap">
          <text class="placeholder-icon">📡</text>
        </view>
        <text class="placeholder-title" :style="{ color: theme.textColor }">网络连接已断开</text>
        <text class="placeholder-desc" :style="{ color: theme.textSecondary }">请检查设备网络连接后重试</text>
        <view class="placeholder-retry" :style="{ background: theme.primaryColor }" @tap="retry">
          <text class="retry-text" :style="{ color: '#fff' }">重新连接</text>
        </view>
        <text class="placeholder-hint" :style="{ color: theme.textMuted }">网络恢复后将自动刷新</text>
      </view>
    </view>

    <!-- 设备未连接/检测中状态 -->
    <view class="placeholder-body" v-else>
      <view class="placeholder-card" :style="{ background: theme.cardColor }">
        <view class="placeholder-icon-wrap" :class="{ pulsing: state === 'checking' }">
          <text class="placeholder-icon">{{ state === 'checking' ? '⏳' : '🏠' }}</text>
        </view>
        <text class="placeholder-title" :style="{ color: theme.textColor }">
          {{ state === 'checking' ? '正在检测设备连接...' : '设备未连接' }}
        </text>
        <text class="placeholder-desc" :style="{ color: theme.textSecondary }">
          {{ state === 'checking' ? '正在为您连接智能家居设备' : '未检测到在线设备，请确保设备已启动并联网' }}
        </text>

        <!-- 检测中：旋转加载指示器 -->
        <view class="loading-spinner" v-if="state === 'checking'">
          <view class="spinner-dot"></view>
          <view class="spinner-dot"></view>
          <view class="spinner-dot"></view>
        </view>

        <!-- 未连接：重试按钮 -->
        <view class="placeholder-retry" v-if="state === 'disconnected'" :style="{ background: theme.primaryColor }" @tap="retry">
          <text class="retry-text" :style="{ color: '#fff' }">重新检测</text>
        </view>
        <text class="placeholder-hint" :style="{ color: theme.textMuted }">
          {{ state === 'checking' ? '请耐心等待...' : '设备连接后将自动加载' }}
        </text>
      </view>
    </view>

    <CustomTabBar :currentIndex="currentTab" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { themeStore } from '@/store/theme.js'
import { isOffline, networkType } from '@/composables/useNetwork.js'

const props = defineProps({
  currentTab: { type: Number, default: 0 },
  // 状态: 'offline' | 'checking' | 'disconnected'
  state: { type: String, default: 'offline' },
})

const theme = computed(() => themeStore.getCurrentTheme())
const emit = defineEmits(['retry'])

const retry = () => {
  if (props.state === 'offline') {
    uni.getNetworkType({
      success(res) {
        networkType.value = res.networkType || 'unknown'
        isOffline.value = res.networkType === 'none'
        if (!isOffline.value) {
          emit('retry')
        }
      }
    })
  } else {
    emit('retry')
  }
}

const goLogin = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('refresh_token')
  uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.placeholder-root {
  min-height: 100vh;
  padding-bottom: 140rpx;
}

.placeholder-nav {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60rpx 24rpx 20rpx;
}

.placeholder-nav-title {
  font-size: 32rpx;
  font-weight: bold;
}

.placeholder-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 48rpx;
}

.placeholder-card {
  width: 100%;
  max-width: 600rpx;
  border-radius: 24rpx;
  padding: 64rpx 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
  text-align: center;
}

.placeholder-icon-wrap {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: rgba(129, 140, 248, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8rpx;
  transition: transform 0.3s ease;

  &.pulsing {
    animation: soft-pulse 2s ease-in-out infinite;
  }
}

.placeholder-icon {
  font-size: 56rpx;
}

.placeholder-title {
  font-size: 30rpx;
  font-weight: 600;
  line-height: 1.4;
}

.placeholder-desc {
  font-size: 26rpx;
  line-height: 1.6;
}

.placeholder-retry {
  border-radius: 40rpx;
  padding: 16rpx 56rpx;
  margin-top: 12rpx;
  cursor: pointer;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }
  &:active {
    opacity: 0.75;
  }
}

.retry-text {
  font-size: 28rpx;
  font-weight: 600;
}

.placeholder-hint {
  font-size: 22rpx;
  margin-top: 4rpx;
}

// 加载动画：三点旋转
.loading-spinner {
  display: flex;
  gap: 12rpx;
  margin-top: 8rpx;
}

.spinner-dot {
  width: 16rpx;
  height: 16rpx;
  border-radius: 50%;
  background: rgba(129, 140, 248, 0.6);
  animation: dot-bounce 1.4s ease-in-out infinite both;

  &:nth-child(1) { animation-delay: -0.32s; }
  &:nth-child(2) { animation-delay: -0.16s; }
  &:nth-child(3) { animation-delay: 0s; }
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

@keyframes soft-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

// ========== 桌面端 ==========
@include desktop {
  .placeholder-root {
    padding-bottom: 0;
  }

  .placeholder-nav {
    padding: 0;
    position: fixed;
    left: $sidebar-width;
    right: 0;
    top: 0;
    height: 56px;
    background: transparent !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    z-index: 10;
    justify-content: flex-start;
    padding-left: $page-padding-x;
  }

  @include desktop-lg {
    .placeholder-nav {
      padding-left: $page-padding-x-lg;
    }
  }

  .placeholder-nav-title {
    font-size: 18px;
  }

  .placeholder-body {
    margin-left: $sidebar-width;
    min-height: calc(100vh - 56px);
    padding: 80px 40px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .placeholder-card {
    max-width: 480px;
    border-radius: 20px;
    padding: 56px 48px;
    gap: 16px;
  }

  .placeholder-icon-wrap {
    width: 96px;
    height: 96px;
  }

  .placeholder-icon {
    font-size: 44px;
  }

  .placeholder-title {
    font-size: 20px;
  }

  .placeholder-desc {
    font-size: 15px;
  }

  .retry-text {
    font-size: 15px;
  }

  .placeholder-hint {
    font-size: 13px;
  }

  .spinner-dot {
    width: 10px;
    height: 10px;
  }
}
</style>
