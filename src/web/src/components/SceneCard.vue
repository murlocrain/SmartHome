<template>
  <view class="scene-card" :style="{ background: `linear-gradient(135deg, ${gradient[0]}, ${gradient[1]})` }" @tap="emit('execute')">
    <view>
      <text class="title">{{ title }}</text>
      <text class="desc">{{ desc }}</text>
    </view>
    <view class="devices">
      <text v-for="item in devices" :key="item.label" class="device">{{ item.label }}：{{ item.value }}</text>
    </view>
    <view class="btn">
      <text class="btn-text">点击启用</text>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  desc?: string
  devices?: { label: string; value: string }[]
  gradient?: [string, string]
}>()

const emit = defineEmits(['execute'])
</script>

<style lang="scss">
.scene-card {
  border-radius: 20rpx;
  padding: 30rpx;
  color: #fff;
  min-height: 280rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.title { font-size: 32rpx; font-weight: bold; }
.desc { font-size: 24rpx; opacity: 0.9; margin-top: 8rpx; }
.device { display: block; font-size: 24rpx; margin: 6rpx 0; }
.btn {
  background: rgba(255,255,255,0.95);
  padding: 20rpx;
  border-radius: 40rpx;
  text-align: center;
}
.btn-text { color: #333; font-size: 26rpx; }
</style>
