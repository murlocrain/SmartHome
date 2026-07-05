<template>
  <view class="page" :style="{ background: theme.bgColor }">
    <view class="header" :style="{ background: theme.cardColor }">
      <text class="header-title" :style="{ color: theme.textColor }">设备仪表盘</text>
      <text class="header-sub" :style="{ color: theme.textSecondary }">
        {{ onlineDevices.length }} 在线 / {{ devices.length }} 总计
      </text>
    </view>

    <view class="device-cards" v-if="devices.length > 0">
      <view
        class="device-card"
        :style="{ background: theme.cardColor }"
        v-for="device in devices"
        :key="device.device_id"
      >
        <!-- 设备头部 -->
        <view class="card-header">
          <view class="card-title-row">
            <view class="status-dot" :class="{ online: device.is_online }" />
            <text class="card-name" :style="{ color: theme.textColor }">{{ device.name || device.device_id }}</text>
          </view>
          <text class="card-type" :style="{ color: theme.primaryColor }">{{ device.device_type_display }}</text>
        </view>

        <!-- 传感器数据 -->
        <view class="sensor-grid" v-if="device.envData">
          <view class="sensor-item">
            <text class="sensor-label" :style="{ color: theme.textMuted }">温度</text>
            <text class="sensor-value" :style="{ color: theme.textColor }">
              {{ fmtTemp(device.envData.temperature) }}
            </text>
          </view>
          <view class="sensor-item">
            <text class="sensor-label" :style="{ color: theme.textMuted }">湿度</text>
            <text class="sensor-value" :style="{ color: theme.textColor }">
              {{ fmtHumi(device.envData.humidity) }}
            </text>
          </view>
          <view class="sensor-item">
            <text class="sensor-label" :style="{ color: theme.textMuted }">光照</text>
            <text class="sensor-value" :style="{ color: theme.textColor }">
              {{ fmtLux(device.envData.light) }}
            </text>
          </view>
          <view class="sensor-item">
            <text class="sensor-label" :style="{ color: theme.textMuted }">人体检测</text>
            <text class="sensor-value" :style="{ color: theme.textColor }">
              {{ device.envData.body_state || '--' }}
            </text>
          </view>
          <view class="sensor-item" v-if="device.envData.lightStatus != null">
            <text class="sensor-label" :style="{ color: theme.textMuted }">灯光</text>
            <text class="sensor-value" :style="{ color: device.envData.lightStatus === 'ON' ? '#22c55e' : theme.textColor }">
              {{ device.envData.lightStatus || '--' }}
            </text>
          </view>
          <view class="sensor-item" v-if="device.envData.motorStatus != null">
            <text class="sensor-label" :style="{ color: theme.textMuted }">电机</text>
            <text class="sensor-value" :style="{ color: device.envData.motorStatus === 'ON' ? '#22c55e' : theme.textColor }">
              {{ device.envData.motorStatus || '--' }}
            </text>
          </view>
        </view>

        <!-- 无数据提示 -->
        <view class="no-data" v-else>
          <text class="no-data-text" :style="{ color: theme.textMuted }">暂无传感数据</text>
        </view>

        <!-- 底部信息 -->
        <view class="card-footer" v-if="device.envData">
          <text class="footer-wifi" :style="{ color: theme.textMuted }">
            WiFi {{ device.envData.wifi_conn_state === 1 ? '已连接' : '未连接' }}
          </text>
          <text class="footer-time" :style="{ color: theme.textMuted }">
            {{ formatTime(device.envData.timestamp) }}
          </text>
        </view>
      </view>
    </view>

    <view class="empty-state" :style="{ background: theme.cardColor }" v-else>
      <text class="empty-icon">📱</text>
      <text class="empty-text" :style="{ color: theme.textSecondary }">暂无设备</text>
      <text class="empty-desc" :style="{ color: theme.textMuted }">请在设备管理页面绑定设备</text>
    </view>

    <CustomTabBar :currentIndex="1" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { getDeviceList } from '@/api'
import { fmtTemp, fmtHumi, fmtLux } from '@/utils/format.js'
import request from '@/api/index.js'
import wsManager from '@/utils/websocket.js'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()
const devices = ref([])

const familyId = computed(() => userStore.currentFamily?.id)

const onlineDevices = computed(() => devices.value.filter(d => d.is_online))

const TYPE_MAP = {
  env_monitor: '环境监测器',
  light: '灯光',
  curtain: '窗帘/电机',
  air_conditioner: '空调',
  aircon: '空调',
}

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const fetchLatestData = async (deviceId) => {
  try {
    const res = await request({
      url: `/data/latest/${deviceId}`,
      method: 'GET'
    })
    return res?.data || null
  } catch {
    return null
  }
}

const updateDeviceEnvData = (deviceId, data) => {
  const device = devices.value.find(d => d.device_id === deviceId)
  if (device) {
    device.envData = {
      temperature: data.sht30_temp_raw ?? data.temperature,
      humidity: data.sht30_humi_raw ?? data.humidity,
      light: data.bh1750_raw ?? data.light,
      body_state: data.pir_gpio === 1 ? '有人' : (data.body_state || '无人'),
      lightStatus: data.lightStatus ?? data.light_status,
      motorStatus: data.motorStatus ?? data.motor_status,
      wifi_conn_state: data.wifi_conn_state,
      timestamp: data.timestamp || new Date().toISOString(),
    }
  }
}

const handleWsMessage = (message) => {
  if (message.type === 'device_update') {
    updateDeviceEnvData(message.device_id, message.data || {})
  }
}

const loadDevices = async () => {
  const fid = familyId.value
  if (!fid) return

  try {
    const res = await getDeviceList(fid)
    if (!res || !res.devices) return

    const list = res.devices.map(d => ({
      device_id: d.device_id,
      device_type: d.device_type,
      device_type_display: TYPE_MAP[d.device_type] || d.device_type,
      name: d.name,
      is_online: d.is_online,
      last_seen: d.last_seen,
      envData: null,
    }))

    // 并行拉取每个设备的最新数据
    await Promise.all(list.map(async (d) => {
      d.envData = await fetchLatestData(d.device_id)
    }))

    devices.value = list
  } catch (e) {
    console.error('加载设备列表失败:', e)
  }
}

onMounted(() => {
  if (!familyId.value) {
    uni.showToast({ title: '请先选择家庭', icon: 'none' })
    setTimeout(() => { uni.reLaunch({ url: '/pages/family/index' }) }, 1500)
    return
  }
  loadDevices()

  // 连接 WebSocket 接收实时数据推送
  wsManager.onMessage(handleWsMessage)
  wsManager.connect(String(familyId.value))
})

onUnmounted(() => {
  wsManager.onMessage(null)
  wsManager.disconnect()
})
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.page {
  min-height: 100vh;
  padding-bottom: 120rpx;
}

.header {
  padding: 32rpx 32rpx 24rpx;
  margin-bottom: 16rpx;
}

.header-title {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
}

.header-sub {
  font-size: 24rpx;
}

.device-cards {
  padding: 0 24rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.device-card {
  border-radius: 20rpx;
  padding: 28rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.status-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #9ca3af;

  &.online {
    background: #22c55e;
  }
}

.card-name {
  font-size: 30rpx;
  font-weight: 600;
}

.card-type {
  font-size: 22rpx;
  padding: 4rpx 16rpx;
  border-radius: 8rpx;
  background: rgba(59, 130, 246, 0.12);
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20rpx;
}

.sensor-item {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.sensor-label {
  font-size: 22rpx;
}

.sensor-value {
  font-size: 28rpx;
  font-weight: 600;
}

.no-data {
  padding: 32rpx 0;
  text-align: center;
}

.no-data-text {
  font-size: 24rpx;
}

.card-footer {
  margin-top: 20rpx;
  display: flex;
  justify-content: space-between;
}

.footer-wifi, .footer-time {
  font-size: 22rpx;
}

.empty-state {
  margin: 120rpx 24rpx;
  border-radius: 20rpx;
  padding: 80rpx 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.empty-icon {
  font-size: 72rpx;
}

.empty-text {
  font-size: 30rpx;
  font-weight: 500;
}

.empty-desc {
  font-size: 24rpx;
}

// ========== 桌面端 ==========
@include desktop {
  .page {
    margin-left: $sidebar-width;
    padding: 32px 40px 40px;
    max-width: $content-max-width;
  }

  .header {
    padding: 0 0 24px;
    margin-bottom: 24px;
    background: transparent !important;
  }

  .header-title {
    font-size: 24px;
  }

  .header-sub {
    font-size: 14px;
  }

  .device-cards {
    padding: 0;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
  }

  .device-card {
    border-radius: 16px;
    padding: 28px;
    transition: box-shadow 0.2s;

    &:hover {
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
  }

  .card-name {
    font-size: 17px;
  }

  .card-type {
    font-size: 13px;
  }

  .status-dot {
    width: 10px;
    height: 10px;
  }

  .sensor-grid {
    gap: 16px;
  }

  .sensor-label {
    font-size: 13px;
  }

  .sensor-value {
    font-size: 16px;
  }

  .no-data-text {
    font-size: 14px;
  }

  .footer-wifi, .footer-time {
    font-size: 12px;
  }

  .empty-state {
    margin: 80px 0;
  }

  .empty-icon {
    font-size: 56px;
  }

  .empty-text {
    font-size: 17px;
  }

  .empty-desc {
    font-size: 14px;
  }
}

// ========== 大屏桌面（1200px+） ==========
@include desktop-lg {
  .page {
    padding: 32px $page-padding-x-lg 44px;
    max-width: $content-max-width-lg;
  }

  .header-title { font-size: 26px; }
  .card-name { font-size: 18px; }
  .sensor-value { font-size: 17px; }

  .device-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: 22px;
  }
}

// ========== 超大屏桌面（1440px+） ==========
@include desktop-xl {
  .page {
    padding: 36px $page-padding-x-lg 48px;
    margin-left: $sidebar-width-lg;
  }

  .device-cards {
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
  }
}
</style>
