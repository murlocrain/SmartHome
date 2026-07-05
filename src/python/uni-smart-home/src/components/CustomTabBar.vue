<template>
  <view class="tab-bar" :style="{ background: theme.cardColor, borderTopColor: theme.borderColor }">
    <view class="tab-item" :class="{ active: currentIndex === 0 }" @tap="switchTab(0)">
      <text class="tab-icon">🏠</text>
      <text class="tab-text" :style="{ color: currentIndex === 0 ? theme.primaryColor : theme.textMuted }">首页</text>
    </view>
    <view class="tab-item" :class="{ active: currentIndex === 1 }" @tap="switchTab(1)">
      <text class="tab-icon">⚡</text>
      <text class="tab-text" :style="{ color: currentIndex === 1 ? theme.primaryColor : theme.textMuted }">设备</text>
    </view>
    <view class="tab-item" :class="{ active: currentIndex === 2 }" @tap="switchTab(2)">
      <text class="tab-icon">🎬</text>
      <text class="tab-text" :style="{ color: currentIndex === 2 ? theme.primaryColor : theme.textMuted }">场景</text>
    </view>
    <view class="tab-item" :class="{ active: currentIndex === 3 }" @tap="switchTab(3)">
      <text class="tab-icon">👤</text>
      <text class="tab-text" :style="{ color: currentIndex === 3 ? theme.primaryColor : theme.textMuted }">我的</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { themeStore } from '@/store/theme.js'

const props = defineProps({
  currentIndex: {
    type: Number,
    default: 0
  }
})

const theme = computed(() => themeStore.getCurrentTheme())

const switchTab = (index) => {
  const urls = [
    '/pages/index/index',
    '/pages/devices/index',
    '/pages/scenes/index',
    '/pages/profile/index'
  ]
  uni.redirectTo({ url: urls[index] })
}
</script>

<style lang="scss">
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 100rpx;
  display: flex;
  justify-content: space-around;
  align-items: center;
  border-top: 1rpx solid;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 999;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  padding: 10rpx 40rpx;

  &.active {
    .tab-icon {
      transform: scale(1.1);
    }
  }
}

.tab-icon {
  font-size: 40rpx;
  transition: transform 0.2s;
}

.tab-text {
  font-size: 22rpx;
  transition: color 0.2s;
}
</style>
