<template>
  <view class="page" :style="{ background: theme.bgColor }">
    <view class="nav-bar" :style="{ background: theme.cardColor }">
      <text class="nav-title" :style="{ color: theme.textColor }">我的</text>
    </view>

    <view class="user-section" :style="{ background: theme.cardColor }">
      <view class="avatar-wrap">
        <view class="avatar">
          <text class="avatar-icon">👤</text>
        </view>
        <view class="online-dot"></view>
      </view>
      <view class="user-info">
        <text class="user-name" :style="{ color: theme.textColor }">{{ userStore.userInfo?.username || '用户' }}</text>
        <text class="user-title" :style="{ color: theme.textSecondary }">{{ userStore.userInfo?.email || '智能家居用户' }}</text>
      </view>
    </view>

    <view class="stats-section">
      <view class="stat-card" :style="{ background: theme.cardColor }">
        <text class="stat-value" :style="{ color: theme.textColor }">{{ deviceCount }}</text>
        <text class="stat-label" :style="{ color: theme.textSecondary }">连接设备</text>
      </view>
      <view class="stat-card" :style="{ background: theme.cardColor }">
        <text class="stat-value" :style="{ color: theme.textColor }">{{ sceneCount }}</text>
        <text class="stat-label" :style="{ color: theme.textSecondary }">执行场景</text>
      </view>
      <view class="stat-card" :style="{ background: theme.cardColor }">
        <text class="stat-value" :style="{ color: theme.textColor }">{{ daysUsed }}</text>
        <text class="stat-label" :style="{ color: theme.textSecondary }">守护天数</text>
      </view>
    </view>

    <view class="section" :style="{ background: theme.cardColor }">
      <text class="section-title" :style="{ color: theme.textSecondary }">显示主题</text>
      <view class="theme-switch">
        <view
          class="theme-btn"
          :class="{ active: themeStore.currentTheme === 'dark' }"
          :style="{
            background: themeStore.currentTheme === 'dark' ? theme.primaryColor : theme.bgColor,
            borderColor: themeStore.currentTheme === 'dark' ? theme.primaryColor : 'transparent'
          }"
          @tap="setTheme('dark')"
        >
          <text class="theme-icon">🌙</text>
          <text class="theme-name" :style="{ color: themeStore.currentTheme === 'dark' ? '#fff' : theme.textColor }">深色</text>
        </view>
        <view
          class="theme-btn"
          :class="{ active: themeStore.currentTheme === 'light' }"
          :style="{
            background: themeStore.currentTheme === 'light' ? theme.primaryColor : theme.bgColor,
            borderColor: themeStore.currentTheme === 'light' ? theme.primaryColor : 'transparent'
          }"
          @tap="setTheme('light')"
        >
          <text class="theme-icon">☀️</text>
          <text class="theme-name" :style="{ color: themeStore.currentTheme === 'light' ? '#fff' : theme.textColor }">浅色</text>
        </view>
        <view
          class="theme-btn"
          :class="{ active: themeStore.currentTheme === 'eye' }"
          :style="{
            background: themeStore.currentTheme === 'eye' ? theme.primaryColor : theme.bgColor,
            borderColor: themeStore.currentTheme === 'eye' ? theme.primaryColor : 'transparent'
          }"
          @tap="setTheme('eye')"
        >
          <text class="theme-icon">🌿</text>
          <text class="theme-name" :style="{ color: themeStore.currentTheme === 'eye' ? '#fff' : theme.textColor }">护眼</text>
        </view>
      </view>
    </view>

    <view class="menu-section" :style="{ background: theme.cardColor }">
      <view class="menu-item" @tap="handleMenu('family')">
        <text class="menu-icon">🏠</text>
        <text class="menu-text" :style="{ color: theme.textColor }">家庭管理</text>
        <text class="menu-badge" :style="{ color: theme.textSecondary }">{{ userStore.familyList.length }}个家庭</text>
        <text class="menu-arrow" :style="{ color: theme.textSecondary }">›</text>
      </view>
      <view class="menu-item" @tap="handleMenu('share')">
        <text class="menu-icon">🔗</text>
        <text class="menu-text" :style="{ color: theme.textColor }">设备共享</text>
        <text class="menu-badge active" :style="{ color: theme.successColor }">已开启</text>
        <text class="menu-arrow" :style="{ color: theme.textSecondary }">›</text>
      </view>
      <view class="menu-item" @tap="handleMenu('notification')">
        <text class="menu-icon">🔔</text>
        <text class="menu-text" :style="{ color: theme.textColor }">消息通知</text>
        <text class="menu-arrow" :style="{ color: theme.textSecondary }">›</text>
      </view>
      <view class="menu-item" @tap="handleMenu('security')">
        <text class="menu-icon">🛡️</text>
        <text class="menu-text" :style="{ color: theme.textColor }">安全设置</text>
        <text class="menu-badge" :style="{ color: theme.textSecondary }">高</text>
        <text class="menu-arrow" :style="{ color: theme.textSecondary }">›</text>
      </view>
    </view>

    <view class="menu-section" :style="{ background: theme.cardColor }">
      <view class="menu-item" @tap="handleMenu('help')">
        <text class="menu-icon">❓</text>
        <text class="menu-text" :style="{ color: theme.textColor }">帮助与反馈</text>
        <text class="menu-arrow" :style="{ color: theme.textSecondary }">›</text>
      </view>
      <view class="menu-item" @tap="handleMenu('about')">
        <text class="menu-icon">ℹ️</text>
        <text class="menu-text" :style="{ color: theme.textColor }">关于智家</text>
        <text class="menu-arrow" :style="{ color: theme.textSecondary }">›</text>
      </view>
      <view class="menu-item logout" @tap="handleMenu('logout')">
        <text class="menu-icon">🚪</text>
        <text class="menu-text" :style="{ color: '#ef4444' }">退出登录</text>
      </view>
    </view>

    <CustomTabBar :currentIndex="3" />
  </view>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { getDeviceList, getFamilySceneRules } from '@/api'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()

// 统计数据（从API获取）
const deviceCount = ref(0)
const sceneCount = ref(0)
const daysUsed = ref(0)

// 计算守护天数（基于用户创建时间）
const familyId = computed(() => userStore.currentFamily?.id)

const setTheme = (themeName) => {
  themeStore.setTheme(themeName)
  const themes = { dark: '深色', light: '浅色', eye: '护眼' }
  uni.showToast({ title: `已切换到${themes[themeName]}模式`, icon: 'none' })
}

const handleMenu = (menu) => {
  const menuActions = {
    family: () => {
      uni.navigateTo({ url: '/pages/family/index' })
    },
    logout: () => {
      userStore.logout()
    },
    share: () => {
      uni.showToast({ title: '设备共享', icon: 'none' })
    },
    notification: () => {
      uni.showToast({ title: '消息通知', icon: 'none' })
    },
    security: () => {
      uni.showToast({ title: '安全设置', icon: 'none' })
    },
    help: () => {
      uni.showToast({ title: '帮助与反馈', icon: 'none' })
    },
    about: () => {
      uni.showToast({ title: '关于智家', icon: 'none' })
    }
  }

  if (menuActions[menu]) {
    menuActions[menu]()
  }
}

// 加载统计数据
const loadStats = async () => {
  if (!familyId.value) return

  try {
    // 加载设备数量
    const deviceRes = await getDeviceList(familyId.value)
    if (deviceRes && deviceRes.data) {
      deviceCount.value = deviceRes.data.length
    }

    // 加载场景数量
    const sceneRes = await getFamilySceneRules(familyId.value)
    if (sceneRes && sceneRes.data) {
      sceneCount.value = sceneRes.data.length
    }

    // 计算守护天数（基于用户创建时间）
    if (userStore.userInfo?.created_at) {
      const createdDate = new Date(userStore.userInfo.created_at)
      const today = new Date()
      const diffDays = Math.floor((today - createdDate) / (1000 * 60 * 60 * 24))
      daysUsed.value = diffDays > 0 ? diffDays : 1
    }
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

onMounted(() => {
  loadStats()
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

.user-section {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 32rpx;
  border-radius: 24rpx;
  margin-top: 24rpx;
}

.avatar-wrap {
  position: relative;
}

.avatar {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-icon {
  font-size: 48rpx;
}

.online-dot {
  position: absolute;
  bottom: 4rpx;
  right: 4rpx;
  width: 20rpx;
  height: 20rpx;
  background: #22c55e;
  border-radius: 50%;
  border: 4rpx solid #1e293b;
}

.user-info {
  flex: 1;
}

.user-name {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
}

.user-title {
  font-size: 24rpx;
}

.stats-section {
  display: flex;
  gap: 16rpx;
  margin-top: 20rpx;
}

.stat-card {
  flex: 1;
  padding: 24rpx 16rpx;
  border-radius: 16rpx;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 22rpx;
}

.section {
  padding: 24rpx;
  border-radius: 20rpx;
  margin-top: 20rpx;
}

.section-title {
  display: block;
  font-size: 24rpx;
  margin-bottom: 20rpx;
}

.theme-switch {
  display: flex;
  gap: 16rpx;
}

.theme-btn {
  flex: 1;
  padding: 20rpx 16rpx;
  border-radius: 12rpx;
  text-align: center;
  border: 2rpx solid transparent;
}

.theme-icon {
  display: block;
  font-size: 36rpx;
  margin-bottom: 8rpx;
}

.theme-name {
  font-size: 22rpx;
}

.menu-section {
  border-radius: 20rpx;
  margin-top: 20rpx;
  overflow: hidden;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  border-bottom: 1rpx solid rgba(0, 0, 0, 0.05);

  &:last-child {
    border-bottom: none;
  }

  &.logout {
    justify-content: center;
    margin-top: 16rpx;
    border-bottom: none;
  }
}

.menu-icon {
  font-size: 32rpx;
  margin-right: 20rpx;
}

.menu-text {
  flex: 1;
  font-size: 28rpx;
}

.menu-badge {
  font-size: 24rpx;
  margin-right: 12rpx;
}

.menu-arrow {
  font-size: 32rpx;
}
</style>
