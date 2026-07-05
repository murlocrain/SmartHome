<template>
  <view class="page" :style="{ background: theme.bgColor }">
    <view class="header" :style="{ background: theme.cardColor }">
      <view class="header-left">
        <text class="greeting" :style="{ color: theme.textSecondary }">{{ greeting }}</text>
        <text class="title" :style="{ color: theme.textColor }">欢迎回家</text>
      </view>
      <view class="header-right">
        <view class="header-btn" :style="{ background: theme.bgColor }">
          <text>🔍</text>
        </view>
        <view class="header-btn notification" :style="{ background: theme.bgColor }">
          <text>🔔</text>
          <view class="badge" v-if="hasNotifications"></view>
        </view>
      </view>
    </view>

    <view class="weather-card" v-if="roomState">
      <view class="weather-main">
        <view class="weather-left">
          <text class="weather-icon">☁️</text>
          <view class="weather-info">
            <text class="weather-desc" :style="{ color: '#fff' }">室内环境</text>
            <text class="weather-location" :style="{ color: 'rgba(255,255,255,0.8)' }">{{ userStore.currentFamily?.name || '我的家' }}</text>
          </view>
        </view>
        <view class="weather-right">
          <text class="weather-temp" :style="{ color: '#fff' }">{{ roomState.temperature || '--' }}°C</text>
        </view>
      </view>
      <view class="weather-detail">
        <view class="detail-item">
          <text class="detail-icon">🏠</text>
          <text class="detail-label" :style="{ color: 'rgba(255,255,255,0.8)' }">室内 {{ roomState.temperature || '--' }}°C</text>
        </view>
        <view class="detail-item">
          <text class="detail-icon">💧</text>
          <text class="detail-label" :style="{ color: 'rgba(255,255,255,0.8)' }">湿度 {{ roomState.humidity || '--' }}%</text>
        </view>
        <view class="detail-item">
          <text class="detail-icon">☀️</text>
          <text class="detail-label" :style="{ color: 'rgba(255,255,255,0.8)' }">光照 {{ roomState.illumination || '--' }} lux</text>
        </view>
        <view class="detail-item">
          <text class="detail-icon">👤</text>
          <text class="detail-label" :style="{ color: 'rgba(255,255,255,0.8)' }">{{ roomState.has_person ? '有人' : '无人' }}</text>
        </view>
      </view>
    </view>

    <view class="stats-row" v-if="devices.length > 0">
      <view class="stat-item" :style="{ background: theme.cardColor }">
        <view class="stat-icon-wrap lights">
          <text class="stat-icon">💡</text>
        </view>
        <view class="stat-info">
          <text class="stat-value" :style="{ color: theme.textColor }">{{ onlineLights }} / {{ totalLights }}</text>
          <text class="stat-label" :style="{ color: theme.textMuted }">灯光已开启</text>
        </view>
      </view>
      <view class="stat-item" :style="{ background: theme.cardColor }">
        <view class="stat-icon-wrap energy">
          <text class="stat-icon">⚡</text>
        </view>
        <view class="stat-info">
          <text class="stat-value" :style="{ color: theme.textColor }">{{ energySaved }}%</text>
          <text class="stat-label" :style="{ color: theme.textMuted }">月度能耗节省</text>
        </view>
      </view>
      <view class="stat-item" :style="{ background: theme.cardColor }">
        <view class="stat-icon-wrap devices">
          <text class="stat-icon">📱</text>
        </view>
        <view class="stat-info">
          <text class="stat-value" :style="{ color: theme.textColor }">{{ onlineDevices }}</text>
          <text class="stat-label" :style="{ color: theme.textMuted }">在线设备</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-header">
        <text class="section-title" :style="{ color: theme.textColor }">快捷控制</text>
      </view>
      <view class="quick-actions">
        <view class="action-card" :style="{ background: theme.cardColor }" @tap="quickAction('allLight')">
          <text class="action-icon">💡</text>
          <text class="action-name" :style="{ color: theme.textColor }">全开灯光</text>
        </view>
        <view class="action-card" :style="{ background: theme.cardColor }" @tap="quickAction('allOff')">
          <text class="action-icon">🔌</text>
          <text class="action-name" :style="{ color: theme.textColor }">全部关闭</text>
        </view>
        <view class="action-card" :style="{ background: theme.cardColor }" @tap="quickAction('sleep')">
          <text class="action-icon">🌙</text>
          <text class="action-name" :style="{ color: theme.textColor }">睡眠模式</text>
        </view>
        <view class="action-card" :style="{ background: theme.cardColor }" @tap="quickAction('away')">
          <text class="action-icon">🚪</text>
          <text class="action-name" :style="{ color: theme.textColor }">离家模式</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-header">
        <text class="section-title" :style="{ color: theme.textColor }">环境监测</text>
      </view>
      <view class="env-card" :style="{ background: theme.cardColor }" v-if="roomState">
        <view class="env-row">
          <view class="env-item">
            <text class="env-icon">🌡️</text>
            <view class="env-info">
              <text class="env-value" :style="{ color: theme.textColor }">{{ roomState.temperature || '--' }}°C</text>
              <text class="env-label" :style="{ color: theme.textMuted }">室内温度</text>
            </view>
          </view>
          <view class="env-divider"></view>
          <view class="env-item">
            <text class="env-icon">💧</text>
            <view class="env-info">
              <text class="env-value" :style="{ color: theme.textColor }">{{ roomState.humidity || '--' }}%</text>
              <text class="env-label" :style="{ color: theme.textMuted }">湿度</text>
            </view>
          </view>
        </view>
        <view class="env-row">
          <view class="env-item">
            <text class="env-icon">☀️</text>
            <view class="env-info">
              <text class="env-value" :style="{ color: theme.textColor }">{{ roomState.illumination || '--' }} lux</text>
              <text class="env-label" :style="{ color: theme.textMuted }">光照强度</text>
            </view>
          </view>
          <view class="env-divider"></view>
          <view class="env-item">
            <text class="env-icon">🫧</text>
            <view class="env-info">
              <text class="env-value" :style="{ color: theme.textColor }">{{ roomState.smoke_detected ? '检测到' : '正常' }}</text>
              <text class="env-label" :style="{ color: theme.textMuted }">烟雾状态</text>
            </view>
          </view>
        </view>
      </view>
      <view class="empty-state" :style="{ background: theme.cardColor }" v-else>
        <text class="empty-icon">📊</text>
        <text class="empty-text" :style="{ color: theme.textSecondary }">暂无环境数据</text>
      </view>
    </view>

    <view class="section">
      <view class="section-header">
        <text class="section-title" :style="{ color: theme.textColor }">常用设备</text>
        <text class="section-more" :style="{ color: theme.primaryColor }" v-if="devices.length > 0" @tap="goToDevices">全部设备 ›</text>
      </view>
      <view class="device-grid" v-if="devices.length > 0">
        <view
          class="device-card"
          :style="{ background: theme.cardColor }"
          v-for="device in devices"
          :key="device.id"
          @tap="handleDevice(device)"
        >
          <view class="device-header">
            <text class="device-icon">{{ device.icon }}</text>
            <view class="device-status" :class="{ online: device.status === 'online' }"></view>
          </view>
          <text class="device-name" :style="{ color: theme.textColor }">{{ device.name }}</text>
          <text class="device-state" :style="{ color: device.status === 'online' ? theme.successColor : theme.textMuted }">{{ device.state }}</text>
        </view>
      </view>
      <view class="empty-state" :style="{ background: theme.cardColor }" v-else>
        <text class="empty-icon">📱</text>
        <text class="empty-text" :style="{ color: theme.textSecondary }">暂无设备</text>
        <text class="empty-desc" :style="{ color: theme.textMuted }">请先添加设备</text>
      </view>
    </view>

    <CustomTabBar :currentIndex="0" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { getDeviceList, getRoomState, getEnvRoomState, initHuaweiDevice } from '@/api'
import wsManager from '@/utils/websocket'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()

// 空数组初始化，无默认数据
const devices = ref([])
const roomState = ref(null)
const loading = ref(true)
const hasNotifications = ref(false)

// 从用户状态管理获取当前家庭ID
const familyId = computed(() => userStore.currentFamily?.id)

// 计算问候语（根据当前时间）
const greeting = computed(() => {
  const hour = new Date().getHours()
  const username = userStore.userInfo?.username || '用户'
  if (hour < 6) return `凌晨好, ${username}`
  if (hour < 9) return `早上好, ${username}`
  if (hour < 12) return `上午好, ${username}`
  if (hour < 14) return `中午好, ${username}`
  if (hour < 17) return `下午好, ${username}`
  if (hour < 19) return `傍晚好, ${username}`
  if (hour < 22) return `晚上好, ${username}`
  return `夜深了, ${username}`
})

// 计算统计数据（基于真实设备数据）
const totalLights = computed(() => devices.value.filter(d => d.device_type === 'light').length)
const onlineLights = computed(() => devices.value.filter(d => d.device_type === 'light' && d.status === 'online').length)
const onlineDevices = computed(() => devices.value.filter(d => d.status === 'online').length)
const energySaved = computed(() => {
  // 基于在线设备数量计算能耗节省比例（示例算法）
  if (devices.value.length === 0) return 0
  const offlineRatio = (devices.value.length - onlineDevices.value) / devices.value.length
  return Math.round(offlineRatio * 100)
})

const handleDevice = (device) => {
  uni.showToast({ title: device.name, icon: 'none' })
}

const goToDevices = () => {
  uni.navigateTo({ url: '/pages/devices/index' })
}

const quickAction = (action) => {
  const actions = {
    allLight: '已开启所有灯光',
    allOff: '已关闭所有设备',
    sleep: '睡眠模式已启动',
    away: '离家模式已启动'
  }
  uni.showToast({ title: actions[action], icon: 'success' })
}

// 加载设备列表
const loadDevices = async () => {
  if (!familyId.value) {
    console.warn('没有选择家庭')
    return
  }

  try {
    const res = await getDeviceList(familyId.value)
    if (res && res.data) {
      devices.value = res.data.map(d => ({
        id: d.id,
        name: d.name,
        device_type: d.device_type,
        icon: d.device_type === 'light' ? '💡' : d.device_type === 'curtain' ? '🪟' : d.device_type === 'air_conditioner' ? '❄️' : '📱',
        status: d.is_online ? 'online' : 'offline',
        state: d.is_online ? '已开启' : '已关闭'
      }))
    }
  } catch (e) {
    console.error('加载设备列表失败:', e)
  }
}

// 加载房间状态数据
const loadRoomState = async () => {
  if (!familyId.value) {
    console.warn('没有选择家庭')
    return
  }

  try {
    const res = await getEnvRoomState(familyId.value)
    if (res && res.data) {
      roomState.value = res.data
    }
  } catch (e) {
    console.error('加载房间状态失败:', e)
  }
}

// 连接WebSocket接收实时数据
const connectWebSocket = () => {
  if (!familyId.value) {
    console.warn('没有选择家庭，无法连接WebSocket')
    return
  }

  console.log('正在连接WebSocket...')
  wsManager.connect(familyId.value)

  // 设置消息回调
  wsManager.onMessage((message) => {
    console.log('收到实时数据:', message)
    
    if (message.type === 'device_update') {
      // 更新环境监测数据
      const data = message.data
      
      // 更新roomState
      if (data.temperature) {
        roomState.value = {
          ...roomState.value,
          temperature: data.temperature,
          humidity: data.humidity,
          illumination: data.illumination,
          smoke_detected: data.smoke === 'detected' || data.smoke === 'alarm',
          has_person: data.body_state === '有人' || data.body_state === 'present' || data.body_state === 'detected'
        }
        
        // 显示提示
        uni.showToast({
          title: `温度: ${data.temperature}°C`,
          icon: 'none',
          duration: 2000
        })
      }
      
      // 更新设备状态
      if (message.device_id) {
        const deviceIndex = devices.value.findIndex(d => d.device_id === message.device_id)
        if (deviceIndex >= 0) {
          devices.value[deviceIndex].status = 'online'
          devices.value[deviceIndex].state = '运行中'
        }
      }
    }
  })
}

onMounted(async () => {
  // 检查是否选择了家庭
  if (!familyId.value) {
    uni.showToast({ title: '请先选择家庭', icon: 'none' })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/family/index' })
    }, 1500)
    return
  }

  await Promise.all([loadDevices(), loadRoomState()])
  
  // 如果没有设备，自动初始化华为云设备
  if (devices.value.length === 0) {
    console.log('未找到设备，正在初始化华为云IoTDA设备...')
    try {
      const res = await initHuaweiDevice(familyId.value)
      if (res && res.data) {
        console.log('华为云设备初始化成功:', res.data)
        // 重新加载设备列表
        await loadDevices()
        uni.showToast({ title: '设备已同步', icon: 'success' })
      }
    } catch (e) {
      console.error('初始化华为云设备失败:', e)
    }
  }
  
  loading.value = false
  
  // 连接WebSocket接收实时数据
  connectWebSocket()
})

onUnmounted(() => {
  // 断开WebSocket连接
  wsManager.disconnect()
})
</script>

<style lang="scss">
.page {
  min-height: 100vh;
  padding: 0 24rpx 140rpx;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 60rpx 24rpx 24rpx;
}

.header-left {
  flex: 1;
}

.greeting {
  display: block;
  font-size: 24rpx;
  margin-bottom: 8rpx;
}

.title {
  font-size: 40rpx;
  font-weight: bold;
}

.header-right {
  display: flex;
  gap: 16rpx;
}

.header-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  position: relative;

  &.notification {
    .badge {
      position: absolute;
      top: 4rpx;
      right: 4rpx;
      width: 16rpx;
      height: 16rpx;
      background: #ef4444;
      border-radius: 50%;
    }
  }
}

.weather-card {
  background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  border-radius: 24rpx;
  padding: 28rpx;
  margin-top: 8rpx;
}

.weather-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.weather-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.weather-icon {
  font-size: 52rpx;
}

.weather-info {
  flex: 1;
}

.weather-desc {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  margin-bottom: 4rpx;
}

.weather-location {
  font-size: 24rpx;
}

.weather-right {
  margin-top: -10rpx;
}

.weather-temp {
  font-size: 64rpx;
  font-weight: bold;
}

.weather-detail {
  display: flex;
  justify-content: space-around;
  margin-top: 24rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.2);
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.detail-icon {
  font-size: 28rpx;
}

.detail-label {
  font-size: 22rpx;
}

.stats-row {
  display: flex;
  gap: 12rpx;
  margin-top: 20rpx;
}

.stat-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 24rpx 16rpx;
  border-radius: 16rpx;
}

.stat-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;

  &.lights {
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  }
  &.energy {
    background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  }
  &.devices {
    background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  }
}

.stat-icon {
  font-size: 32rpx;
}

.stat-info {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 4rpx;
}

.stat-label {
  font-size: 20rpx;
}

.section {
  margin-top: 32rpx;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.section-title {
  font-size: 30rpx;
  font-weight: bold;
}

.section-more {
  font-size: 24rpx;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.action-card {
  width: calc(50% - 6rpx);
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 24rpx;
  border-radius: 16rpx;
}

.action-icon {
  font-size: 40rpx;
}

.action-name {
  font-size: 26rpx;
  font-weight: 500;
}

.env-card {
  border-radius: 20rpx;
  padding: 24rpx;
}

.env-row {
  display: flex;
  align-items: center;
}

.env-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 0;
}

.env-icon {
  font-size: 36rpx;
}

.env-info {
  flex: 1;
}

.env-value {
  display: block;
  font-size: 28rpx;
  font-weight: bold;
  margin-bottom: 4rpx;
}

.env-label {
  font-size: 22rpx;
}

.env-divider {
  width: 1rpx;
  height: 60rpx;
  background: rgba(0, 0, 0, 0.08);
}

.device-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.device-card {
  width: calc(50% - 8rpx);
  padding: 24rpx;
  border-radius: 16rpx;
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.device-icon {
  font-size: 40rpx;
}

.device-status {
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #94a3b8;

  &.online {
    background: #22c55e;
  }
}

.device-name {
  display: block;
  font-size: 26rpx;
  font-weight: 500;
  margin-bottom: 6rpx;
}

.device-state {
  font-size: 22rpx;
}

.empty-state {
  padding: 60rpx 24rpx;
  border-radius: 20rpx;
  text-align: center;
}

.empty-icon {
  font-size: 80rpx;
  display: block;
  margin-bottom: 24rpx;
}

.empty-text {
  display: block;
  font-size: 28rpx;
  margin-bottom: 12rpx;
}

.empty-desc {
  font-size: 24rpx;
}
</style>