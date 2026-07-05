<template>
  <view class="page" :style="{ background: theme.bgColor }">
    <view class="nav-bar" :style="{ background: theme.cardColor }">
      <text class="nav-title" :style="{ color: theme.textColor }">场景模式</text>
    </view>

    <view class="scene-list">
      <view
        class="scene-card"
        v-for="scene in scenes"
        :key="scene.id"
        :class="{ active: scene.active }"
        :style="{ background: scene.active ? theme.primaryColor : theme.cardColor }"
        @tap="executeScene(scene)"
      >
        <view class="scene-icon">{{ scene.icon }}</view>
        <view class="scene-info">
          <text class="scene-name" :style="{ color: scene.active ? '#fff' : theme.textColor }">{{ scene.name }}</text>
          <text class="scene-desc" :style="{ color: scene.active ? 'rgba(255,255,255,0.8)' : theme.textSecondary }">{{ scene.desc }}</text>
        </view>
        <view class="scene-status" v-if="scene.active">
          <text class="status-icon">✓</text>
          <text class="status-text" :style="{ color: '#fff' }">使用中</text>
        </view>
      </view>
    </view>

    <CustomTabBar :currentIndex="2" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { getFamilySceneRules, createSceneWebSocket } from '@/api'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()

// 空数组初始化，无默认数据
const scenes = ref([])

// 从用户状态管理获取当前家庭ID
const familyId = computed(() => userStore.currentFamily?.id)

const executeScene = (scene) => {
  scenes.value.forEach(s => s.active = false)
  scene.active = true
  uni.showToast({ title: `${scene.name} 已启动`, icon: 'success' })
}

const addScene = () => {
  uni.showToast({ title: '添加场景', icon: 'none' })
}

// 加载场景规则列表
const loadScenes = async () => {
  if (!familyId.value) {
    console.warn('没有选择家庭')
    return
  }

  try {
    const res = await getFamilySceneRules(familyId.value)
    if (res && res.data) {
      scenes.value = res.data.map(s => ({
        id: s.id,
        name: s.name,
        icon: '✨',
        desc: s.scene_id || '',
        active: false
      }))
    }
  } catch (e) {
    console.error('加载场景规则失败:', e)
  }
}

onMounted(() => {
  // 检查是否选择了家庭
  if (!familyId.value) {
    uni.showToast({ title: '请先选择家庭', icon: 'none' })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/family/index' })
    }, 1500)
    return
  }

  loadScenes()
})
</script>

<style lang="scss">
.page {
  min-height: 100vh;
  padding: 0 24rpx 140rpx;
}

.nav-bar {
  padding: 60rpx 24rpx 20rpx;
}

.nav-title {
  font-size: 32rpx;
  font-weight: bold;
}

.scene-list {
  margin-top: 24rpx;
}

.scene-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx;
  border-radius: 20rpx;
  margin-bottom: 16rpx;
  transition: all 0.3s;

  &.active {
    transform: translateX(8rpx);
  }
}

.scene-icon {
  font-size: 52rpx;
}

.scene-info {
  flex: 1;
}

.scene-name {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  margin-bottom: 6rpx;
}

.scene-desc {
  font-size: 24rpx;
}

.scene-status {
  display: flex;
  align-items: center;
  gap: 8rpx;
  background: rgba(255, 255, 255, 0.2);
  padding: 8rpx 16rpx;
  border-radius: 20rpx;
}

.status-icon {
  font-size: 24rpx;
  color: #fff;
}

.status-text {
  font-size: 22rpx;
}
</style>