<template>
  <view class="page">
    <!-- 顶部状态栏 -->
    <view class="status-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header">
        <view class="logo">
          <text class="logo-icon">📊</text>
          <text class="app-name">数据分析看板</text>
        </view>
        <view class="header-actions">
          <view class="nav-btn" @tap="goToAlert">
            <text>🔮 预警</text>
          </view>
          <view class="date-range" @tap="showDatePicker">
            <text class="date-text">{{ dateRange }}</text>
            <text class="date-arrow">▼</text>
          </view>
          <view class="export-btn" @tap="exportData">
            <text>导出报表</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 顶部：实时状态卡片 -->
    <view class="status-cards">
      <view class="status-card temp">
        <text class="card-icon">🌡️</text>
        <view class="card-info">
          <text class="card-value">{{ realtime.temperature }}°C</text>
          <text class="card-label">当前温度</text>
        </view>
      </view>
      <view class="status-card humidity">
        <text class="card-icon">💧</text>
        <view class="card-info">
          <text class="card-value">{{ realtime.humidity }}%</text>
          <text class="card-label">当前湿度</text>
        </view>
      </view>
      <view class="status-card light">
        <text class="card-icon">💡</text>
        <view class="card-info">
          <text class="card-value">{{ realtime.lightLevel }}</text>
          <text class="card-label">当前光照</text>
        </view>
      </view>
      <view class="status-card person">
        <text class="card-icon">{{ realtime.occupied ? '🟢' : '⚪' }}</text>
        <view class="card-info">
          <text class="card-value">{{ realtime.occupied ? '有人' : '无人' }}</text>
          <text class="card-label">人员状态</text>
        </view>
      </view>
      <view class="status-card scene">
        <text class="card-icon">🏠</text>
        <view class="card-info">
          <text class="card-value">{{ realtime.scene || '-' }}</text>
          <text class="card-label">当前场景</text>
        </view>
      </view>
    </view>

    <!-- 主内容区 -->
    <view class="main-content">
      <!-- 中部：环境参数时序图（上） + 活动强度与场景时序图（下） -->
      <view class="middle-section">
        <!-- 环境参数变化图表（温度、湿度、光照合并） -->
        <view class="chart-card full-width">
          <view class="card-header">
            <text class="card-title">环境参数变化</text>
            <view class="legend">
              <view class="legend-item"><view class="line" style="background:#f59e0b"></view>温度 (°C)</view>
              <view class="legend-item"><view class="line" style="background:#3b82f6"></view>湿度 (%)</view>
              <view class="legend-item"><view class="line" style="background:#10b981"></view>光照 (lux)</view>
            </view>
          </view>
          <view class="chart-body dual-axis">
            <view class="axis-left">
              <text v-for="(val, i) in leftYLabels" :key="'ly'+i" class="y-axis-label" :style="{bottom: (i/4*100)+'%'}">{{ val }}</text>
            </view>
            <view class="chart-area">
              <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="chart-svg">
                <defs>
                  <linearGradient id="tempGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(245,158,11,0.2)" />
                    <stop offset="100%" stop-color="rgba(245,158,11,0)" />
                  </linearGradient>
                  <linearGradient id="humidityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(59,130,246,0.15)" />
                    <stop offset="100%" stop-color="rgba(59,130,246,0)" />
                  </linearGradient>
                  <linearGradient id="lightGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(16,185,129,0.15)" />
                    <stop offset="100%" stop-color="rgba(16,185,129,0)" />
                  </linearGradient>
                </defs>
                <line v-for="i in 5" :key="'gh'+i" x1="0" :y1="i*10" x2="100" :y2="i*10" stroke="rgba(255,255,255,0.06)" stroke-width="0.3" />
                <polygon :points="'0,60 ' + envTempPoints + ' 100,60'" fill="url(#tempGradient)" />
                <polyline :points="envTempPoints" fill="none" stroke="#f59e0b" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round" />
                <polygon :points="'0,60 ' + envHumidityPoints + ' 100,60'" fill="url(#humidityGradient)" />
                <polyline :points="envHumidityPoints" fill="none" stroke="#3b82f6" stroke-width="0.6" stroke-linecap="round" stroke-linejoin="round" opacity="0.8" />
                <polygon :points="'0,60 ' + envLightPoints + ' 100,60'" fill="url(#lightGradient)" />
                <polyline :points="envLightPoints" fill="none" stroke="#10b981" stroke-width="0.6" stroke-linecap="round" stroke-linejoin="round" opacity="0.8" />
              </svg>
            </view>
            <view class="axis-right">
              <text v-for="(val, i) in rightYLabels" :key="'ry'+i" class="y-axis-label" :style="{bottom: (i/4*100)+'%'}">{{ val }}</text>
            </view>
            <view class="axis-bottom">
              <text v-for="(label, i) in xLabels" :key="i" class="axis-label" :style="{left: (i/Math.max(xLabels.length-1,1)*100)+'%'}">{{ label }}</text>
            </view>
          </view>
        </view>

        <!-- 活动强度与场景时序图 -->
        <view class="chart-card full-width">
          <view class="card-header">
            <text class="card-title">活动强度与场景</text>
            <view class="legend">
              <view class="legend-item"><view class="line" style="background:#6366f1"></view>活动强度</view>
            </view>
          </view>
          <view class="chart-body">
            <view class="chart-area">
              <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="chart-svg">
                <defs>
                  <linearGradient id="activityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="rgba(99,102,241,0.25)" />
                    <stop offset="100%" stop-color="rgba(99,102,241,0)" />
                  </linearGradient>
                </defs>
                <line v-for="i in 5" :key="'ah'+i" x1="0" :y1="i*10" x2="100" :y2="i*10" stroke="rgba(255,255,255,0.06)" stroke-width="0.3" />
                <polygon :points="'0,60 ' + activityPoints + ' 100,60'" fill="url(#activityGradient)" />
                <polyline :points="activityPoints" fill="none" stroke="#6366f1" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round" />
                <circle v-for="(pt, i) in scenePoints" :key="i" :cx="pt.x" :cy="pt.y" :r="1" :fill="pt.color" opacity="0.8" />
                <circle v-for="(pt, i) in scenePoints" :key="'ring'+i" :cx="pt.x" :cy="pt.y" :r="2" fill="none" :stroke="pt.color" stroke-width="0.3" opacity="0.4" />
              </svg>
            </view>
            <view class="axis-bottom">
              <text v-for="(label, i) in xLabels" :key="i" class="axis-label" :style="{left: (i/Math.max(xLabels.length-1,1)*100)+'%'}">{{ label }}</text>
            </view>
          </view>
          <view class="scene-legend">
            <view v-for="(item, i) in sceneColors" :key="i" class="scene-legend-item">
              <view class="dot" :style="{ background: item.color }"></view>
              <text class="name">{{ item.name }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 下部区域 -->
      <view class="bottom-section">
        <!-- 左下：24小时活动热力图 -->
        <view class="chart-card heatmap-card">
          <view class="card-header">
            <text class="card-title">24小时活动热力图</text>
            <text class="card-subtitle">点击时段查看详情</text>
          </view>
          <view class="heatmap-body">
            <view class="heatmap-row labels">
              <text class="heatmap-cell hour-label"></text>
              <text v-for="d in weekDays" :key="d" class="heatmap-cell day-label">{{ d }}</text>
            </view>
            <view v-for="h in heatmapHours" :key="h" class="heatmap-row">
              <text class="heatmap-cell hour-label">{{ h }}h</text>
              <view
                v-for="(val, di) in heatmapData[h]"
                :key="di"
                class="heatmap-cell"
                :style="{ background: heatmapColor(val) }"
                @tap="selectHour(h, di)"
              >
                <text v-if="selectedHour === h && selectedDay === di" class="heatmap-dot">●</text>
              </view>
            </view>
            <view class="heatmap-legend">
              <text class="legend-label">低</text>
              <view class="legend-bar">
                <view v-for="i in 5" :key="i" class="legend-seg" :style="{ background: heatmapColor((i-1)/4) }"></view>
              </view>
              <text class="legend-label">高</text>
            </view>
          </view>
        </view>

        <!-- 右下：场景分布饼图 + 每日作息时间线 -->
        <view class="right-bottom">
          <!-- 场景分布饼图 -->
          <view class="chart-card pie-card">
            <view class="card-header">
              <text class="card-title">场景分布</text>
            </view>
            <view class="pie-body">
              <svg viewBox="0 0 100 100" class="pie-svg">
                <g v-for="(seg, i) in pieSegments" :key="i">
                  <path :d="seg.path" :fill="seg.color" stroke="rgba(15,23,42,0.8)" stroke-width="0.5" />
                </g>
              </svg>
              <view class="pie-legend">
                <view v-for="(item, i) in sceneDistribution" :key="i" class="pie-legend-item">
                  <view class="dot" :style="{ background: item.color }"></view>
                  <text class="name">{{ item.name }}</text>
                  <text class="value">{{ item.percent }}%</text>
                </view>
              </view>
            </view>
          </view>

          <!-- 每日作息时间线 -->
          <view class="chart-card timeline-card">
            <view class="card-header">
              <text class="card-title">每日作息时间线</text>
            </view>
            <view class="timeline-body">
              <view v-for="(day, i) in dailyTimeline" :key="i" class="timeline-row">
                <text class="timeline-date">{{ day.date }}</text>
                <view class="timeline-track">
                  <view v-for="h in [0,6,12,18,24]" :key="h" class="timeline-marker" :style="{left: (h/24*100)+'%'}">
                    <text class="marker-line"></text>
                    <text class="marker-label">{{ h }}h</text>
                  </view>
                  <view v-if="day.firstMotion" class="timeline-event" :style="{left: (timeToPercent(day.firstMotion)/24*100)+'%'}">
                    <text class="event-icon">🚶</text>
                    <text class="event-time">{{ formatTime(day.firstMotion) }}</text>
                  </view>
                  <view v-if="day.lastMotion" class="timeline-event" :style="{left: (timeToPercent(day.lastMotion)/24*100)+'%'}">
                    <text class="event-icon">🏠</text>
                    <text class="event-time">{{ formatTime(day.lastMotion) }}</text>
                  </view>
                  <view v-if="day.sleepStart" class="timeline-event" :style="{left: (timeToPercent(day.sleepStart)/24*100)+'%'}">
                    <text class="event-icon">😴</text>
                    <text class="event-time">{{ formatTime(day.sleepStart) }}</text>
                  </view>
                  <view v-if="day.sleepEnd" class="timeline-event" :style="{left: (timeToPercent(day.sleepEnd)/24*100)+'%'}">
                    <text class="event-icon">☀️</text>
                    <text class="event-time">{{ formatTime(day.sleepEnd) }}</text>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- 底部：灯光/电机状态切换记录 -->
      <view class="chart-card state-log-card">
        <view class="card-header">
          <text class="card-title">灯光/电机状态切换记录</text>
        </view>
        <view class="state-log-body">
          <view v-for="(log, i) in stateLogs.slice(0, 8)" :key="i" class="state-log-item">
            <text class="log-time">{{ formatDateTime(log.timestamp) }}</text>
            <view class="log-state">
              <text v-if="log.lightStatus !== null" class="log-item">
                <text class="icon">💡</text>
                <text :class="log.lightStatus ? 'on' : 'off'">{{ log.lightStatus ? '开' : '关' }}</text>
              </text>
              <text v-if="log.motorStatus !== null" class="log-item">
                <text class="icon">⚙️</text>
                <text :class="log.motorStatus ? 'on' : 'off'">{{ log.motorStatus ? '开' : '关' }}</text>
              </text>
            </view>
          </view>
        </view>
      </view>
    </view>

    <CustomTabBar v-if="isDesktop" :current-index="4" />
    <CustomTabBar v-if="!isDesktop" :current-index="4" />

    <view v-if="showDetailModal" class="modal-overlay" @tap="closeDetailModal">
      <view class="modal-content" @tap.stop>
        <view class="modal-header">
          <text class="modal-title">时段详情</text>
          <text class="modal-close" @tap="closeDetailModal">✕</text>
        </view>
        <view v-if="selectedDetail" class="modal-body">
          <view class="detail-date">
            <text class="detail-day">{{ selectedDetail.day }}</text>
            <text class="detail-hour">{{ selectedDetail.hour }}:00 - {{ selectedDetail.hour + 1 }}:00</text>
          </view>
          <view class="detail-grid">
            <view class="detail-card">
              <text class="detail-icon">📊</text>
              <text class="detail-label">活动总量</text>
              <text class="detail-value">{{ selectedDetail.totalMotion }}</text>
            </view>
            <view class="detail-card">
              <text class="detail-icon">⚡</text>
              <text class="detail-label">平均活动指数</text>
              <text class="detail-value">{{ selectedDetail.avgActivity }}</text>
            </view>
            <view class="detail-card">
              <text class="detail-icon">🏠</text>
              <text class="detail-label">主要场景</text>
              <text class="detail-value">{{ selectedDetail.topScene }}</text>
            </view>
            <view class="detail-card">
              <text class="detail-icon">🌡️</text>
              <text class="detail-label">平均温度</text>
              <text class="detail-value">{{ selectedDetail.avgTemp }}{{ selectedDetail.avgTemp !== '-' ? '°C' : '' }}</text>
            </view>
          </view>
          <view class="detail-info">
            <text class="info-text">共 {{ selectedDetail.recordCount }} 条记录</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { useBreakpoint } from '@/composables/useBreakpoint.js'

const { isDesktop } = useBreakpoint()

const statusBarHeight = ref(44)
const dateRange = ref('近3天')
const selectedHour = ref(null)
const selectedDay = ref(null)
const showDetailModal = ref(false)

// 数据源
const fullData = ref([])
const sleepData = ref([])
const sceneData = ref([])
const allFullData = ref([])
const allSleepData = ref([])
const allSceneData = ref([])
const realtime = ref({ temperature: 0, humidity: 0, lightLevel: 0, occupied: false, scene: '' })

// 加载数据
async function loadData() {
  try {
    // 并行请求 API
    const [tsRes, rtRes] = await Promise.all([
      fetch('/api/v1/analysis/timeseries?days=7').then(r => r.json()).catch(() => null),
      fetch('/api/v1/analysis/realtime').then(r => r.json()).catch(() => null),
    ])

    if (rtRes && rtRes.code === 200) {
      const d = rtRes.data
      realtime.value = {
        temperature: d.temperature != null ? d.temperature.toFixed(1) : '0.0',
        humidity: d.humidity != null ? d.humidity.toFixed(1) : '0.0',
        lightLevel: d.light != null ? d.light.toFixed(0) : '-',
        occupied: d.pir_detected === true,
        scene: d.scene || '-'
      }
    }

    if (tsRes && tsRes.code === 200) {
      const { full_data, sleep_data, scene_data } = tsRes.data

      if (full_data && full_data.length) {
        const processed = full_data.map(row => ({
          timestamp: new Date(row.timestamp),
          temperature: row.temperature || 0,
          humidity: row.humidity || 0,
          gas: row.combustible_gas || 0,
          motion: row.motion_detected || 0,
          occupied: row.predicted_occupied || 0,
          probability: row.occupied_probability || 0
        }))
        allFullData.value = processed
        fullData.value = processed
      }

      if (sleep_data && sleep_data.length) {
        const processed = sleep_data.map(row => ({
          timestamp: new Date(row.timestamp),
          date: row.date,
          hour: row.hour || 0,
          motion5min: row.motion_5min_sum || 0,
          activityIndex: row.activity_index || 0,
          firstMotion: row.first_motion,
          lastMotion: row.last_motion,
          sleepStart: row.sleep_start,
          sleepEnd: row.sleep_end
        }))
        allSleepData.value = processed
        sleepData.value = processed
      }

      if (scene_data && scene_data.length) {
        const processed = scene_data.map(row => ({
          timestamp: new Date(row.timestamp),
          scene: row.scene || '',
          lightStatus: row.light_status_num != null ? row.light_status_num : null,
          motorStatus: row.motor_status_num != null ? row.motor_status_num : null,
          lightChanged: row.light_changed || 0,
          lightLevel: row.bh1750_raw || null
        }))
        allSceneData.value = processed
        sceneData.value = processed
      }
    }

    // 如果 API 无数据则使用兜底数据
    if (!allFullData.value.length && !allSleepData.value.length) {
      useFallbackData()
    } else {
      filterDataByRange(1)
    }
  } catch (e) {
    console.error('数据加载失败', e)
    useFallbackData()
  }
}

function useFallbackData() {
  const now = new Date()
  const base = new Date(now.getTime() - 7 * 24 * 3600000)
  const envFallback = []
  const sleepFallback = []
  const sceneFallback = []

  for (let i = 0; i < 7 * 24; i++) {
    const t = new Date(base.getTime() + i * 3600000)
    const hour = t.getHours()
    envFallback.push({
      timestamp: t,
      temperature: 26 + Math.sin(i / 12 * Math.PI) * 4 + Math.random() * 2,
      humidity: 45 + Math.cos(i / 12 * Math.PI) * 15 + Math.random() * 5,
      gas: 110 + Math.random() * 30,
      motion: hour >= 8 && hour <= 22 ? Math.random() * 5 : 0,
      occupied: hour >= 7 && hour <= 23 ? 1 : 0,
      probability: hour >= 7 && hour <= 23 ? 0.8 + Math.random() * 0.2 : Math.random() * 0.3
    })
    const isStartOfDay = hour === 7
    const isEndOfDay = hour === 22
    const isSleepStart = hour === 23
    const isSleepEnd = hour === 6
    sleepFallback.push({
      timestamp: t,
      date: `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')}`,
      hour,
      motion5min: hour >= 6 && hour <= 23 ? Math.random() * 10 : 0,
      activityIndex: hour >= 6 && hour <= 23 ? Math.random() * 5 : 0,
      firstMotion: isStartOfDay ? '07:30:00' : null,
      lastMotion: isEndOfDay ? '22:30:00' : null,
      sleepStart: isSleepStart ? '23:00:00' : null,
      sleepEnd: isSleepEnd ? '06:30:00' : null
    })
    const sceneWeights = [0.1, 0.4, 0.3, 0.2]
    const rand = Math.random()
    let sceneIndex = 0
    let cumulative = 0
    for (let j = 0; j < sceneWeights.length; j++) {
      cumulative += sceneWeights[j]
      if (rand < cumulative) { sceneIndex = j; break }
    }
    const scenes = ['离家', '居家', '睡眠', '活动']
    sceneFallback.push({
      timestamp: t,
      scene: scenes[sceneIndex],
      lightStatus: Math.random() > 0.5 ? 1 : 0,
      motorStatus: Math.random() > 0.7 ? 1 : 0,
      lightChanged: Math.random() > 0.9 ? 1 : 0,
      lightLevel: Math.random() * 200
    })
  }

  allFullData.value = envFallback
  allSleepData.value = sleepFallback
  allSceneData.value = sceneFallback
  fullData.value = envFallback
  sleepData.value = sleepFallback
  sceneData.value = sceneFallback

  realtime.value = {
    temperature: 28.5,
    humidity: 50.0,
    lightLevel: 120,
    occupied: true,
    scene: '居家'
  }

  filterDataByRange(1)
}

function goToAlert() {
  uni.navigateTo({ url: '/pages/data-alert/index' })
}

function filterDataByRange(index) {
  if (!allFullData.value.length) return
  const now = new Date()
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  let startTime = startOfDay
  switch (index) {
    case 0: startTime = startOfDay; break
    case 1: startTime = new Date(startOfDay.getTime() - 2 * 24 * 60 * 60 * 1000); break
    case 2: const dayOfWeek = now.getDay(); const diff = dayOfWeek === 0 ? 6 : dayOfWeek - 1; startTime = new Date(startOfDay.getTime() - diff * 24 * 60 * 60 * 1000); break
    case 3: startTime = new Date(now.getFullYear(), now.getMonth(), 1); break
    default: return
  }
  fullData.value = allFullData.value.filter(row => new Date(row.timestamp) >= startTime && new Date(row.timestamp) <= now)
  sleepData.value = allSleepData.value.filter(row => new Date(row.timestamp) >= startTime && new Date(row.timestamp) <= now)
  sceneData.value = allSceneData.value.filter(row => new Date(row.timestamp) >= startTime && new Date(row.timestamp) <= now)
  uni.showToast({ title: `已切换到${dateRange.value}`, icon: 'success' })
}

const xLabels = computed(() => {
  if (!fullData.value.length) return []
  const sampled = fullData.value.filter((_, i) => i % Math.ceil(fullData.value.length / 6) === 0)
  return sampled.map(d => `${d.timestamp.getHours()}:00`)
})

const leftYLabels = computed(() => ['35', '30', '25', '20'])
const rightYLabels = computed(() => ['300', '225', '150', '75', '0'])

function getX(i, len) {
  if (len <= 1) return 50
  return (i / (len - 1)) * 100
}

function tempToSvg(t) {
  const vals = fullData.value.map(d => d.temperature)
  const max = Math.max(...vals, 35)
  const min = Math.min(...vals, 20)
  return 60 - ((t - min) / (max - min)) * 60
}

function humidityToSvg(h) {
  const vals = fullData.value.map(d => d.humidity)
  const max = Math.max(...vals, 80)
  const min = Math.min(...vals, 30)
  return 60 - ((h - min) / (max - min)) * 60
}

function lightToSvg(l) {
  const vals = sceneData.value.map(d => d.lightLevel || 0)
  const max = Math.max(...vals, 300)
  const min = 0
  return 60 - ((l - min) / (max - min)) * 60
}

function activityToSvg(a) {
  const vals = sleepData.value.map(d => d.activityIndex)
  const max = Math.max(...vals, 10)
  const min = 0
  return 60 - ((a - min) / (max - min)) * 60
}

const envTempPoints = computed(() => {
  if (!fullData.value.length) return ''
  const len = fullData.value.length
  return fullData.value.map((d, i) => `${getX(i, len)},${tempToSvg(d.temperature)}`).join(' ')
})

const envHumidityPoints = computed(() => {
  if (!fullData.value.length) return ''
  const len = fullData.value.length
  return fullData.value.map((d, i) => `${getX(i, len)},${humidityToSvg(d.humidity)}`).join(' ')
})

const envLightPoints = computed(() => {
  if (!sceneData.value.length) return ''
  const len = sceneData.value.length
  return sceneData.value.map((d, i) => `${getX(i, len)},${lightToSvg(d.lightLevel || 0)}`).join(' ')
})

const activityPoints = computed(() => {
  if (!sleepData.value.length) return ''
  const len = sleepData.value.length
  return sleepData.value.map((d, i) => `${getX(i, len)},${activityToSvg(d.activityIndex)}`).join(' ')
})

const sceneColors = [
  { name: '离家', color: '#ef4444' },
  { name: '居家', color: '#3b82f6' },
  { name: '室内活动', color: '#10b981' },
  { name: '睡眠', color: '#a855f7' },
  { name: '其他', color: '#64748b' }
]

const scenePoints = computed(() => {
  if (!sceneData.value.length) return []
  const len = sceneData.value.length
  return sceneData.value.map((d, i) => {
    const color = sceneColors.find(c => c.name === d.scene)?.color || '#94a3b8'
    return { x: getX(i, len), y: 55, color }
  }).filter((_, i) => i % Math.ceil(len / 10) === 0)
})

const weekDays = ['一', '二', '三', '四', '五', '六', '日']
const heatmapHours = [...Array(24).keys()]

const heatmapData = computed(() => {
  const data = {}
  heatmapHours.forEach(h => { data[h] = [0, 0, 0, 0, 0, 0, 0] })
  allSleepData.value.forEach(r => {
    if (!r.date || r.hour === undefined) return
    const date = new Date(r.date)
    const dayIndex = date.getDay()
    const dIndex = dayIndex === 0 ? 6 : dayIndex - 1
    if (!data[r.hour]) data[r.hour] = [0, 0, 0, 0, 0, 0, 0]
    data[r.hour][dIndex] += r.motion5min || 0
  })
  const maxVal = Math.max(...Object.values(data).flat(), 1)
  Object.keys(data).forEach(h => { data[h] = data[h].map(v => Math.min(v / maxVal, 1)) })
  return data
})

function heatmapColor(v) {
  const colors = ['#1e293b', '#1e3a5f', '#1e4a7f', '#1e5a9f', '#3b82f6', '#60a5fa']
  const idx = Math.min(Math.floor(v * colors.length), colors.length - 1)
  return colors[idx]
}

const selectedDetail = computed(() => {
  if (selectedHour.value === null || selectedDay.value === null) return null
  const h = selectedHour.value
  const di = selectedDay.value
  const fullWeekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const dayName = fullWeekDays[di]
  const matchingRecords = allSleepData.value.filter(r =>
    r.hour === h && r.date && new Date(r.date).getDay() === (di === 6 ? 0 : di + 1)
  )
  const motionTotal = matchingRecords.reduce((sum, r) => sum + (r.motion5min || 0), 0)
  const avgActivity = matchingRecords.length > 0
    ? matchingRecords.reduce((sum, r) => sum + (r.activityIndex || 0), 0) / matchingRecords.length
    : 0
  const matchingScenes = allSceneData.value.filter(r => {
    const timestamp = new Date(r.timestamp)
    return timestamp.getHours() === h && timestamp.getDay() === (di === 6 ? 0 : di + 1)
  })
  const sceneCounts = {}
  matchingScenes.forEach(r => { if (r.scene) sceneCounts[r.scene] = (sceneCounts[r.scene] || 0) + 1 })
  const topScene = Object.entries(sceneCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '无数据'
  const avgTemp = matchingRecords.length > 0
    ? matchingRecords.reduce((sum, r) => sum + (r.temperature || 0), 0) / matchingRecords.length
    : 0
  return {
    hour: h, day: dayName,
    totalMotion: motionTotal.toFixed(1),
    avgActivity: avgActivity.toFixed(2),
    topScene,
    recordCount: matchingRecords.length,
    avgTemp: avgTemp > 0 ? avgTemp.toFixed(1) : '-'
  }
})

function selectHour(h, di) {
  selectedHour.value = h
  selectedDay.value = di
  showDetailModal.value = true
}

function closeDetailModal() {
  showDetailModal.value = false
}

const sceneDistribution = computed(() => {
  const counts = {}
  sceneData.value.forEach(r => { if (r.scene) { counts[r.scene] = (counts[r.scene] || 0) + 1 } })
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1
  return Object.entries(counts).map(([name, count]) => {
    const color = sceneColors.find(c => c.name === name)?.color || '#94a3b8'
    return { name, count, percent: Math.round((count / total) * 100), color }
  }).sort((a, b) => b.count - a.count)
})

const pieSegments = computed(() => {
  const cx = 50, cy = 50, r = 35
  let angle = -90
  const total = sceneDistribution.value.reduce((s, i) => s + i.count, 0) || 1
  return sceneDistribution.value.map(item => {
    const pct = item.count / total
    const angleRange = pct * 360
    const startRad = (angle * Math.PI) / 180
    const endRad = ((angle + angleRange) * Math.PI) / 180
    const x1 = cx + r * Math.cos(startRad)
    const y1 = cy + r * Math.sin(startRad)
    const x2 = cx + r * Math.cos(endRad)
    const y2 = cy + r * Math.sin(endRad)
    const largeArc = angleRange > 180 ? 1 : 0
    const path = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`
    angle += angleRange
    return { color: item.color, path }
  })
})

const dailyTimeline = computed(() => {
  const days = {}
  sleepData.value.forEach(r => {
    if (!r.date) return
    const dateParts = r.date.split('-')
    const displayDate = dateParts.length >= 3 ? `${dateParts[1]}-${dateParts[2]}` : r.date
    if (!days[r.date]) {
      days[r.date] = { date: displayDate, firstMotion: null, lastMotion: null, sleepStart: null, sleepEnd: null }
    }
    if (r.firstMotion && !days[r.date].firstMotion) days[r.date].firstMotion = r.firstMotion
    if (r.lastMotion && (!days[r.date].lastMotion || r.lastMotion > days[r.date].lastMotion)) {
      days[r.date].lastMotion = r.lastMotion
    }
    if (r.sleepStart && (!days[r.date].sleepStart || r.sleepStart < days[r.date].sleepStart)) {
      days[r.date].sleepStart = r.sleepStart
    }
    if (r.sleepEnd && (!days[r.date].sleepEnd || r.sleepEnd > days[r.date].sleepEnd)) {
      days[r.date].sleepEnd = r.sleepEnd
    }
  })
  return Object.values(days).slice(-5)
})

function formatTime(timeStr) {
  if (!timeStr) return ''
  const timePart = timeStr.split(' ').pop() || timeStr
  return timePart.slice(0, 5)
}

function timeToPercent(timeStr) {
  if (!timeStr) return 0
  const timePart = timeStr.split(' ').pop() || timeStr
  const parts = timePart.split(':')
  const hour = parseInt(parts[0]) || 0
  const minute = parseInt(parts[1]) || 0
  return hour + minute / 60
}

const stateLogs = computed(() => {
  const logs = []
  const lightChanges = sceneData.value.filter(r => r.lightChanged === 1 && r.lightStatus !== null)
  const motorChanges = sceneData.value.filter(r => r.motorStatus !== null && (r.motorStatus === 1 || r.motorStatus === 0))
  lightChanges.forEach(r => { logs.push({ timestamp: r.timestamp, lightStatus: r.lightStatus, motorStatus: null }) })
  motorChanges.forEach(r => {
    const existing = logs.find(l => Math.abs(l.timestamp - r.timestamp) < 30000)
    if (existing) { existing.motorStatus = r.motorStatus }
    else { logs.push({ timestamp: r.timestamp, lightStatus: null, motorStatus: r.motorStatus }) }
  })
  return logs.sort((a, b) => b.timestamp - a.timestamp)
})

function formatDateTime(dt) {
  return `${dt.getMonth() + 1}/${dt.getDate()} ${String(dt.getHours()).padStart(2, '0')}:${String(dt.getMinutes()).padStart(2, '0')}`
}

function showDatePicker() {
  uni.showActionSheet({
    itemList: ['今日', '近3天', '本周', '本月'],
    success: (res) => {
      const options = ['今日', '近3天', '本周', '本月']
      dateRange.value = options[res.tapIndex]
      filterDataByRange(res.tapIndex)
    }
  })
}

function exportData() {
  try {
    const now = new Date()
    const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
    const timeStr = `${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}`
    const filename = `数据分析报表_${dateStr}_${timeStr}.csv`

    const csvHeaders = ['时间戳', '温度(°C)', '湿度(%)', '燃气浓度', '人员状态', '存在概率', '场景', '光照状态', '电机状态']
    const csvRows = fullData.value.map((d, i) => {
      const scene = sceneData.value.find(s => Math.abs(s.timestamp - d.timestamp) < 15000)
      return [
        d.timestamp.toISOString(), d.temperature.toFixed(2), d.humidity.toFixed(2),
        d.gas.toFixed(2), d.occupied, d.probability.toFixed(2),
        scene?.scene || '-', scene?.lightStatus ?? '-', scene?.motorStatus ?? '-'
      ]
    })
    const csvContent = [csvHeaders.join(','), ...csvRows.map(row => row.map(cell => `"${cell}"`).join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    uni.showToast({ title: '导出成功', icon: 'success' })
  } catch (e) {
    console.error('导出失败', e)
    uni.showToast({ title: '导出失败', icon: 'error' })
  }
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

* { box-sizing: border-box; }

.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 0 2vw 2vh;
  overflow-y: auto;
  overflow-x: hidden;
}

// 桌面端：占满导航栏右侧全部可用区域，无 max-width 限制
@include desktop {
  .page {
    margin-left: $sidebar-width;
    padding: 0 1.5vw 1.5vh;
    width: calc(100vw - #{$sidebar-width});
    max-width: none;
  }
}

@include desktop-lg {
  .page {
    margin-left: $sidebar-width-lg;
    width: calc(100vw - #{$sidebar-width-lg});
    max-width: none;
  }
}

.status-bar { background: rgba(15, 23, 42, 0.98); }

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6vh 0;
}

.logo { display: flex; align-items: center; gap: 0.5vw; }
.logo-icon { font-size: clamp(18px, 1.8vw, 28px); }
.app-name { font-size: clamp(14px, 1.5vw, 22px); font-weight: bold; color: #fff; }

.header-actions { display: flex; align-items: center; gap: 0.5vw; }

.nav-btn {
  background: rgba(99, 102, 241, 0.2);
  border: 1rpx solid rgba(99, 102, 241, 0.3);
  padding: 0.4vh 0.8vw;
  border-radius: 1vw;
  font-size: clamp(12px, 1vw, 16px);
  color: #a5b4fc;
}

.date-range {
  display: flex; align-items: center; gap: 0.3vw;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.4vh 0.8vw; border-radius: 1vw;
}
.date-text { font-size: clamp(12px, 1vw, 16px); color: #fff; }
.date-arrow { font-size: clamp(10px, 0.8vw, 14px); color: #94a3b8; }

.export-btn {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  padding: 0.4vh 0.8vw; border-radius: 1vw;
  font-size: clamp(12px, 1vw, 16px); color: #fff;
}

.status-cards { display: flex; gap: 0.5vw; margin-top: 0.6vh; overflow-x: auto; }

.status-card {
  flex: 1; min-width: 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.8vw; padding: 0.8vh 0.5vw;
  display: flex; flex-direction: column; align-items: center; gap: 0.3vh;
  border: 1rpx solid rgba(255, 255, 255, 0.05);
  &.temp { border-color: rgba(245, 158, 11, 0.3); }
  &.humidity { border-color: rgba(59, 130, 246, 0.3); }
  &.light { border-color: rgba(251, 191, 36, 0.3); }
  &.person { border-color: rgba(34, 197, 94, 0.3); }
  &.scene { border-color: rgba(99, 102, 241, 0.3); }
}

.card-icon { font-size: clamp(14px, 1.6vw, 24px); }
.card-info { display: flex; flex-direction: column; align-items: center; gap: 0.1vh; }
.card-value { font-size: clamp(12px, 1.2vw, 18px); font-weight: bold; color: #fff; }
.card-label { font-size: clamp(10px, 0.8vw, 14px); color: #94a3b8; }

.main-content { margin-top: 0.4vh; display: flex; flex-direction: column; gap: 0.8vh; }
.middle-section { display: flex; flex-direction: column; gap: 0.8vh; }

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.8vw; padding: 1vh 1vw;
  border: 1rpx solid rgba(255, 255, 255, 0.05);
}
.full-width { width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5vh; }
.card-title { font-size: clamp(13px, 1.1vw, 18px); font-weight: bold; color: #fff; }
.card-subtitle { font-size: clamp(10px, 0.8vw, 14px); color: #64748b; }

.legend { display: flex; gap: 0.6vw; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 0.3vw; font-size: clamp(10px, 0.8vw, 13px); color: #94a3b8; }
.legend-item .line { width: 1.2vw; height: 0.2vh; border-radius: 1px; }
.legend-item .dot { width: 0.5vw; height: 0.5vw; min-width: 6px; min-height: 6px; border-radius: 50%; }

// 图表主体 — 使用 vh 高度，根据 viewport 自适应
.chart-body { position: relative; height: 22vh; min-height: 120px; display: flex; align-items: flex-start; }
.chart-body.dual-axis { flex-direction: row; }
.chart-area { position: relative; flex: 1; height: calc(22vh - 3.5vh); min-height: 100px; }
.axis-left { position: relative; width: 3.5vw; min-width: 36px; height: calc(22vh - 3.5vh); min-height: 100px; flex-shrink: 0; }
.axis-right { position: relative; width: 3.5vw; min-width: 36px; height: calc(22vh - 3.5vh); min-height: 100px; flex-shrink: 0; }

.chart-svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.y-axis-label { position: absolute; font-size: clamp(9px, 0.7vw, 12px); color: #64748b; text-align: right; padding-right: 0.3vw; transform: translateY(50%); }
.axis-right .y-axis-label { text-align: left; padding-left: 0.3vw; padding-right: 0; }

.axis-bottom { position: absolute; bottom: 0; left: 3.5vw; right: 3.5vw; height: 3vh; }
.axis-bottom .axis-label { position: absolute; transform: translateX(-50%); font-size: clamp(9px, 0.7vw, 12px); color: #64748b; }

.scene-legend { display: flex; gap: 0.6vw; margin-top: 0.4vh; flex-wrap: wrap; }
.scene-legend-item { display: flex; align-items: center; gap: 0.3vw; font-size: clamp(10px, 0.8vw, 13px); color: #94a3b8; }
.scene-legend-item .dot { width: 0.5vw; height: 0.5vw; min-width: 6px; min-height: 6px; border-radius: 50%; }
.scene-legend-item .name { font-size: clamp(10px, 0.8vw, 13px); }

.bottom-section { display: flex; flex-direction: column; gap: 0.8vh; }
.heatmap-card { flex: 1; }
.heatmap-body { display: flex; flex-direction: column; gap: 0.1vh; }
.heatmap-row { display: flex; align-items: center; }
.heatmap-row.labels { border-bottom: 1rpx solid rgba(255,255,255,0.08); padding-bottom: 0.3vh; margin-bottom: 0.1vh; }
.heatmap-cell { flex: 1; height: 1.6vh; min-height: 14px; border-radius: 0.2vw; display: flex; align-items: center; justify-content: center; font-size: clamp(8px, 0.65vw, 11px); }
.heatmap-cell.hour-label { width: 2vw; min-width: 18px; flex: none; color: #64748b; font-size: clamp(8px, 0.7vw, 12px); }
.heatmap-cell.day-label { color: #64748b; font-size: clamp(8px, 0.7vw, 12px); }
.heatmap-dot { color: #fff; font-size: clamp(8px, 0.7vw, 12px); }
.heatmap-legend { display: flex; align-items: center; gap: 0.4vw; margin-top: 0.4vh; }
.legend-label { font-size: clamp(9px, 0.7vw, 12px); color: #64748b; }
.legend-bar { display: flex; flex: 1; height: 0.6vh; min-height: 5px; border-radius: 0.3vh; overflow: hidden; }
.legend-seg { flex: 1; }

.right-bottom { display: flex; flex-direction: column; gap: 0.8vh; }
.pie-card { flex: 1; }
.pie-body { display: flex; align-items: center; gap: 1vw; }
.pie-svg { width: 16vh; height: 16vh; min-width: 90px; min-height: 90px; flex-shrink: 0; }
.pie-legend { display: flex; flex-direction: column; gap: 0.4vh; }
.pie-legend-item { display: flex; align-items: center; gap: 0.3vw; font-size: clamp(10px, 0.8vw, 13px); }
.pie-legend-item .dot { width: 0.5vw; height: 0.5vw; min-width: 6px; min-height: 6px; border-radius: 50%; }
.pie-legend-item .name { color: #94a3b8; flex: 1; }
.pie-legend-item .value { color: #cbd5e1; font-weight: bold; }

.timeline-card { flex: 1; }
.timeline-row { display: flex; align-items: center; margin-bottom: 0.8vh; }
.timeline-date { width: 3.5vw; min-width: 44px; font-size: clamp(10px, 0.8vw, 13px); color: #94a3b8; flex-shrink: 0; }
.timeline-track { flex: 1; height: 2vh; min-height: 18px; background: rgba(255,255,255,0.05); border-radius: 0.5vh; position: relative; }
.timeline-marker { position: absolute; bottom: -0.3vh; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.marker-line { width: 1px; height: 2.2vh; background: rgba(255,255,255,0.1); }
.marker-label { font-size: clamp(8px, 0.6vw, 11px); color: #64748b; margin-top: 0.1vh; }
.timeline-event { position: absolute; top: -0.5vh; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; }
.event-icon { font-size: clamp(9px, 0.7vw, 12px); }
.event-time { font-size: clamp(7px, 0.55vw, 10px); color: #94a3b8; }

.state-log-card { margin-top: 0; }
.state-log-item { display: flex; align-items: center; padding: 0.6vh 0.8vw; background: rgba(255,255,255,0.03); border-radius: 0.6vw; margin-bottom: 0.4vh; gap: 0.6vw; }
.log-time { font-size: clamp(10px, 0.85vw, 14px); color: #94a3b8; flex-shrink: 0; }
.log-state { display: flex; gap: 0.8vw; }
.log-item { display: flex; align-items: center; gap: 0.2vw; font-size: clamp(10px, 0.85vw, 14px); }
.log-item .icon { font-size: clamp(10px, 0.8vw, 14px); }
.log-item .on { color: #22c55e; }
.log-item .off { color: #94a3b8; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 2vw; }
.modal-content { background: #1e293b; border-radius: 1.2vw; padding: 1.5vh 1.5vw; width: 90%; max-width: 500px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1vh; }
.modal-title { font-size: clamp(15px, 1.3vw, 20px); font-weight: bold; color: #fff; }
.modal-close { font-size: clamp(15px, 1.3vw, 20px); color: #94a3b8; padding: 0.4vw; }
.detail-date { text-align: center; margin-bottom: 1vh; }
.detail-day { font-size: clamp(13px, 1.1vw, 18px); color: #fff; font-weight: bold; display: block; }
.detail-hour { font-size: clamp(11px, 0.9vw, 15px); color: #94a3b8; margin-top: 0.1vh; display: block; }
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6vw; }
.detail-card { background: rgba(255,255,255,0.05); border-radius: 0.7vw; padding: 0.8vh 0.8vw; text-align: center; }
.detail-icon { font-size: clamp(15px, 1.3vw, 22px); display: block; margin-bottom: 0.3vh; }
.detail-label { font-size: clamp(10px, 0.8vw, 14px); color: #94a3b8; display: block; }
.detail-value { font-size: clamp(13px, 1.1vw, 18px); font-weight: bold; color: #fff; display: block; margin-top: 0.1vh; }
.detail-info { text-align: center; margin-top: 0.6vh; }
.info-text { font-size: clamp(10px, 0.85vw, 14px); color: #64748b; }
</style>
