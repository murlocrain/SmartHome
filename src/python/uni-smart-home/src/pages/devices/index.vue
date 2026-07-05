<template>
  <view class="page" :style="{ background: theme.bgColor }">
    <view class="nav-bar" :style="{ background: theme.cardColor }">
      <text class="nav-title" :style="{ color: theme.textColor }">设备管理</text>
      <view class="add-btn" :style="{ background: theme.primaryColor }" @tap="addDevice">
        <text class="add-icon" :style="{ color: '#fff' }">+</text>
      </view>
    </view>

    <view class="page-header">
      <text class="page-title" :style="{ color: theme.textColor }">设备管理</text>
      <text class="page-desc" :style="{ color: theme.textSecondary }">共 {{ totalDevices }} 个设备，{{ onlineDevices }} 个在线</text>
    </view>

    <view class="quick-controls">
      <view class="control-btn" :style="{ background: theme.cardColor }" @tap="toggleAllLights">
        <view class="control-icon-wrap yellow">
          <text class="control-icon">💡</text>
        </view>
        <text class="control-name" :style="{ color: theme.textColor }">全开灯光</text>
      </view>
      <view class="control-btn" :style="{ background: theme.cardColor }" @tap="toggleAllCurtains">
        <view class="control-icon-wrap blue">
          <text class="control-icon">🪟</text>
        </view>
        <text class="control-name" :style="{ color: theme.textColor }">全开窗帘</text>
      </view>
      <view class="control-btn" :style="{ background: theme.cardColor }" @tap="toggleAllAircons">
        <view class="control-icon-wrap purple">
          <text class="control-icon">❄️</text>
        </view>
        <text class="control-name" :style="{ color: theme.textColor }">全开空调</text>
      </view>
    </view>

    <view class="tab-bar" :style="{ background: theme.cardColor }">
      <view
        class="tab-item"
        :class="{ active: activeTab === 'light' }"
        :style="{
          background: activeTab === 'light' ? theme.primaryColor : 'transparent',
          color: activeTab === 'light' ? '#fff' : theme.textColor
        }"
        @tap="activeTab = 'light'"
      >
        <text>💡 灯光控制</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'curtain' }"
        :style="{
          background: activeTab === 'curtain' ? theme.primaryColor : 'transparent',
          color: activeTab === 'curtain' ? '#fff' : theme.textColor
        }"
        @tap="activeTab = 'curtain'"
      >
        <text>🪟 窗帘控制</text>
      </view>
      <view
        class="tab-item"
        :class="{ active: activeTab === 'aircon' }"
        :style="{
          background: activeTab === 'aircon' ? theme.primaryColor : 'transparent',
          color: activeTab === 'aircon' ? '#fff' : theme.textColor
        }"
        @tap="activeTab = 'aircon'"
      >
        <text>❄️ 空调控制</text>
      </view>
    </view>

    <view class="device-list">
      <view
        class="device-card"
        :style="{ background: theme.cardColor }"
        v-for="device in currentDevices"
        :key="device.id"
      >
        <view class="device-header">
          <view class="device-icon-wrap" :style="{ background: device.iconBg }">
            <text class="device-icon">{{ device.icon }}</text>
          </view>
          <view class="device-info">
            <text class="device-name" :style="{ color: theme.textColor }">{{ device.name }}</text>
            <text class="device-state" :style="{ color: theme.successColor }">{{ device.state }}</text>
          </view>
          <switch
            :checked="device.status"
            @change="(e) => toggleDevice(device, e.detail.value)"
            :color="theme.primaryColor"
          />
        </view>
        <view class="device-controls" v-if="device.hasBrightness">
          <view class="control-row">
            <text class="control-label" :style="{ color: theme.textSecondary }">亮度</text>
            <text class="control-value" :style="{ color: theme.textColor }">{{ device.brightness }}%</text>
          </view>
          <slider
            :value="device.brightness"
            :min="0"
            :max="100"
            :activeColor="theme.primaryColor"
            backgroundColor="rgba(0,0,0,0.1)"
            block-size="20"
            @change="(e) => updateBrightness(device, e.detail.value)"
          />
        </view>
        <view class="device-controls" v-if="device.hasColorTemp">
          <view class="control-row">
            <text class="control-label" :style="{ color: theme.textSecondary }">色温</text>
            <text class="control-value" :style="{ color: theme.textColor }">{{ device.colorTemp }}K</text>
          </view>
          <slider
            :value="device.colorTemp"
            :min="2700"
            :max="6500"
            activeColor="#f59e0b"
            backgroundColor="rgba(0,0,0,0.1)"
            block-size="20"
            @change="(e) => updateColorTemp(device, e.detail.value)"
          />
        </view>
      </view>
    </view>

    <CustomTabBar :currentIndex="1" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { getDeviceList, initHuaweiDevice } from '@/api'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()
const activeTab = ref('light')

// 空数组初始化，无默认数据
const lightDevices = ref([])
const curtainDevices = ref([])
const airconDevices = ref([])

// 从用户状态管理获取当前家庭ID
const familyId = computed(() => userStore.currentFamily?.id)

// 计算统计数据
const totalDevices = computed(() => lightDevices.value.length + curtainDevices.value.length + airconDevices.value.length)
const onlineDevices = computed(() => {
  const lights = lightDevices.value.filter(d => d.status).length
  const curtains = curtainDevices.value.filter(d => d.status).length
  const aircons = airconDevices.value.filter(d => d.status).length
  return lights + curtains + aircons
})

const currentDevices = computed(() => {
  switch (activeTab.value) {
    case 'curtain': return curtainDevices.value
    case 'aircon': return airconDevices.value
    default: return lightDevices.value
  }
})

const toggleDevice = (device, status) => {
  device.status = status
  device.state = status ? (device.name.includes('空调') ? '运行中' : '已打开') : '已关闭'

  // 通过WebSocket发送设备控制命令
  console.log('控制设备:', device.id, status ? 'on' : 'off')
}

const updateBrightness = (device, value) => {
  device.brightness = value
  // 通过WebSocket发送亮度更新命令
  console.log('更新亮度:', device.id, value)
}

const updateColorTemp = (device, value) => {
  device.colorTemp = value
  // 通过WebSocket发送色温更新命令
  console.log('更新色温:', device.id, value)
}

const toggleAllLights = () => {
  if (lightDevices.value.length === 0) {
    uni.showToast({ title: '暂无灯光设备', icon: 'none' })
    return
  }
  const allOn = lightDevices.value.every(d => d.status)
  lightDevices.value.forEach(d => {
    d.status = !allOn
    d.state = d.status ? '运行中' : '已关闭'
    d.brightness = d.status ? 50 : 0
  })
  uni.showToast({ title: allOn ? '已关闭所有灯光' : '已开启所有灯光', icon: 'success' })
}

const toggleAllCurtains = () => {
  if (curtainDevices.value.length === 0) {
    uni.showToast({ title: '暂无窗帘设备', icon: 'none' })
    return
  }
  const allOn = curtainDevices.value.every(d => d.status)
  curtainDevices.value.forEach(d => {
    d.status = !allOn
    d.state = d.status ? '已打开' : '已关闭'
  })
  uni.showToast({ title: allOn ? '已关闭所有窗帘' : '已开启所有窗帘', icon: 'success' })
}

const toggleAllAircons = () => {
  if (airconDevices.value.length === 0) {
    uni.showToast({ title: '暂无空调设备', icon: 'none' })
    return
  }
  const allOn = airconDevices.value.every(d => d.status)
  airconDevices.value.forEach(d => {
    d.status = !allOn
    d.state = d.status ? '26°C 制冷' : '已关闭'
  })
  uni.showToast({ title: allOn ? '已关闭所有空调' : '已开启所有空调', icon: 'success' })
}

const addDevice = async () => {
  if (!familyId.value) {
    uni.showToast({ title: '请先选择家庭', icon: 'none' })
    return
  }
  
  uni.showModal({
    title: '添加设备',
    content: '是否同步华为云IoTDA环境监测设备？',
    success: async (res) => {
      if (res.confirm) {
        try {
          uni.showLoading({ title: '正在同步...' })
          const result = await initHuaweiDevice(familyId.value)
          uni.hideLoading()
          
          if (result && result.data) {
            uni.showToast({ title: '设备同步成功', icon: 'success' })
            // 重新加载设备列表
            await loadDevices()
          }
        } catch (e) {
          uni.hideLoading()
          console.error('同步设备失败:', e)
          uni.showToast({ title: '同步失败: ' + (e.data?.detail || '未知错误'), icon: 'none' })
        }
      }
    }
  })
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
      // 根据设备类型分类
      const lights = res.data.filter(d => d.device_type === 'light')
      const curtains = res.data.filter(d => d.device_type === 'curtain')
      const aircons = res.data.filter(d => d.device_type === 'aircon' || d.device_type === 'air_conditioner')

      if (lights.length > 0) {
        lightDevices.value = lights.map(d => ({
          id: d.id,
          name: d.name,
          icon: '💡',
          iconBg: 'linear-gradient(135deg, #f97316 0%, #fb923c 100%)',
          state: d.is_online ? '运行中' : '已关闭',
          status: d.is_online,
          brightness: d.capabilities?.brightness ? (d.brightness || 50) : 0,
          colorTemp: d.capabilities?.colorTemp ? (d.colorTemp || 4000) : 4000,
          hasBrightness: d.capabilities?.brightness,
          hasColorTemp: d.capabilities?.colorTemp
        }))
      }

      if (curtains.length > 0) {
        curtainDevices.value = curtains.map(d => ({
          id: d.id,
          name: d.name,
          icon: '🪟',
          iconBg: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)',
          state: d.is_online ? '已打开' : '已关闭',
          status: d.is_online
        }))
      }

      if (aircons.length > 0) {
        airconDevices.value = aircons.map(d => ({
          id: d.id,
          name: d.name,
          icon: '❄️',
          iconBg: 'linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%)',
          state: d.is_online ? d.state || '运行中' : '已关闭',
          status: d.is_online
        }))
      }
    }
  } catch (e) {
    console.error('加载设备列表失败:', e)
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

  loadDevices()
})
</script>

<style lang="scss">
.page {
  min-height: 100vh;
  padding: 0 24rpx 140rpx;
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 60rpx 24rpx 20rpx;
}

.nav-title {
  font-size: 32rpx;
  font-weight: bold;
}

.add-btn {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-icon {
  font-size: 32rpx;
  font-weight: bold;
}

.page-header {
  padding: 24rpx 0;
}

.page-title {
  display: block;
  font-size: 36rpx;
  font-weight: bold;
  margin-bottom: 8rpx;
}

.page-desc {
  font-size: 24rpx;
}

.quick-controls {
  display: flex;
  gap: 16rpx;
}

.control-btn {
  flex: 1;
  padding: 20rpx 16rpx;
  border-radius: 16rpx;
  text-align: center;
}

.control-icon-wrap {
  width: 64rpx;
  height: 64rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12rpx;

  &.yellow {
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  }
  &.blue {
    background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  }
  &.purple {
    background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
  }
}

.control-icon {
  font-size: 32rpx;
}

.control-name {
  font-size: 22rpx;
}

.tab-bar {
  display: flex;
  gap: 12rpx;
  padding: 12rpx;
  border-radius: 16rpx;
  margin-top: 20rpx;
}

.tab-item {
  flex: 1;
  padding: 16rpx;
  border-radius: 12rpx;
  text-align: center;
  font-size: 24rpx;
}

.device-list {
  margin-top: 20rpx;
}

.device-card {
  padding: 24rpx;
  border-radius: 20rpx;
  margin-bottom: 16rpx;
}

.device-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.device-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.device-icon {
  font-size: 36rpx;
}

.device-info {
  flex: 1;
}

.device-name {
  display: block;
  font-size: 28rpx;
  font-weight: 500;
  margin-bottom: 4rpx;
}

.device-state {
  font-size: 22rpx;
}

.device-controls {
  margin-top: 20rpx;
  padding-top: 20rpx;
  border-top: 1rpx solid rgba(0, 0, 0, 0.05);
}

.control-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.control-label {
  font-size: 24rpx;
}

.control-value {
  font-size: 24rpx;
}

slider {
  margin: 0;
}
</style>