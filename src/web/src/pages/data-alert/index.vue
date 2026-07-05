<template>
  <view class="page">
    <view class="status-bar" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="header">
        <view class="logo">
          <view class="back-btn" @tap="goBack">
            <text>← 返回分析</text>
          </view>
          <text class="logo-icon">🔮</text>
          <text class="app-name">AI智能预警</text>
        </view>
        <view class="header-actions">
          <view class="date-range" @tap="showDatePicker">
            <text class="date-text">{{ dateRange }}</text>
            <text class="date-arrow">▼</text>
          </view>
        </view>
      </view>
    </view>

    <view class="main-content">
      <!-- 模块1：当前预警状态卡片 -->
      <view class="status-cards">
        <view class="status-card" :class="{ anomaly: todayIsAnomalous }">
          <text class="card-icon">{{ todayIsAnomalous ? '🚨' : '✅' }}</text>
          <view class="card-info">
            <text class="card-value">{{ todayIsAnomalous ? '异常' : '正常' }}</text>
            <text class="card-label">今日状态</text>
          </view>
        </view>
        <view class="status-card count">
          <text class="card-icon">🔴</text>
          <view class="card-info">
            <text class="card-value">{{ todayAnomalyCount }}</text>
            <text class="card-label">异常点数</text>
          </view>
        </view>
        <view class="status-card zscore">
          <text class="card-icon">📊</text>
          <view class="card-info">
            <text class="card-value">{{ todayMaxZscore.toFixed(2) }}</text>
            <text class="card-label">最高 z-score</text>
          </view>
        </view>
        <view class="status-card time">
          <text class="card-icon">🕐</text>
          <view class="card-info">
            <text class="card-value">{{ latestTime }}</text>
            <text class="card-label">检测时间</text>
          </view>
        </view>
      </view>

      <!-- 模块2：夜间异常时间线图 -->
      <view class="chart-card timeline-card">
        <view class="card-header">
          <text class="card-title">夜间异常时间线</text>
          <view class="legend">
            <view class="legend-item"><view class="line" style="background:#3b82f6"></view>运动次数</view>
            <view class="legend-item"><view class="line" style="background:#f59e0b"></view>z-score</view>
            <view class="legend-item"><view class="line" style="background:#ef4444;stroke-dasharray:4,2"></view>异常阈值</view>
            <view class="legend-item"><view class="dot" style="background:#ef4444"></view>异常点</view>
          </view>
        </view>
        <view class="chart-body" @tap="handleChartAreaClick">
          <view class="axis-left">
            <text v-for="(label, i) in leftYLabels" :key="'yl'+i" class="axis-label-left" :style="{ bottom: ((i / (leftYLabels.length - 1)) * 100) + '%' }">{{ label }}</text>
          </view>
          <view class="chart-area">
            <svg viewBox="0 0 100 60" preserveAspectRatio="none" class="chart-svg">
              <line v-for="i in 5" :key="'gh'+i" x1="0" :y1="i*12" x2="100" :y2="i*12" stroke="rgba(255,255,255,0.05)" stroke-width="0.2" />
              <polyline :points="motionLinePoints" fill="none" stroke="#3b82f6" stroke-width="0.5" stroke-linecap="round" stroke-linejoin="round" />
              <polyline :points="zscoreLinePoints" fill="none" stroke="#f59e0b" stroke-width="0.4" stroke-linecap="round" stroke-linejoin="round" opacity="0.8" />
              <line x1="0" :y1="thresholdY" x2="100" :y2="thresholdY" stroke="#ef4444" stroke-width="0.4" stroke-dasharray="2,2" />
              <circle v-for="(pt, i) in anomalyPoints" :key="i" :cx="pt.x" :cy="pt.y" r="1.2" fill="#ef4444" />
              <g v-for="(item, idx) in clickablePoints" :key="'click-'+idx">
                <circle :cx="item.x" :cy="item.y" r="3" fill="transparent" class="clickable-point" @click.stop="handlePointClick(idx, $event)" />
              </g>
            </svg>
            <view v-if="tooltipVisible && tooltipData" class="chart-tooltip" :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }">
              <view class="tooltip-header">{{ formatTime(tooltipData.timestamp) }}</view>
              <view class="tooltip-row"><text class="tooltip-label">运动次数：</text><text class="tooltip-value">{{ tooltipData.motion_5min_sum }}</text></view>
              <view class="tooltip-row"><text class="tooltip-label">z-score：</text><text class="tooltip-value" :class="{ high: tooltipData.motion_zscore > 2.5 }">{{ tooltipData.motion_zscore.toFixed(2) }}</text></view>
              <view class="tooltip-row"><text class="tooltip-label">活动指数：</text><text class="tooltip-value">{{ tooltipData.activity_index.toFixed(2) }}</text></view>
              <view class="tooltip-row" v-if="tooltipData.sht30_temp_raw"><text class="tooltip-label">温度：</text><text class="tooltip-value">{{ tooltipData.sht30_temp_raw.toFixed(1) }}°C</text></view>
              <view class="tooltip-row" v-if="tooltipData.is_anomaly_point === 1"><text class="tooltip-label">状态：</text><text class="tooltip-value high">🚨 异常点</text></view>
            </view>
          </view>
          <view class="axis-right">
            <text v-for="(label, i) in rightYLabels" :key="'yr'+i" class="axis-label-right" :style="{ bottom: ((i / (rightYLabels.length - 1)) * 100) + '%' }">{{ label }}</text>
          </view>
          <view class="axis-bottom">
            <text v-for="(label, i) in xLabels" :key="i" class="axis-label" :style="{left: xLabelPositions[i] + '%'}">{{ label }}</text>
          </view>
        </view>
      </view>

      <!-- 模块3：异常点详情列表 -->
      <view class="chart-card list-card">
        <view class="card-header">
          <text class="card-title">异常点详情</text>
          <text class="card-subtitle">共 {{ anomalyList.length }} 条记录</text>
        </view>
        <scroll-view class="list-scroll" scroll-y>
          <view v-for="(item, i) in anomalyList.slice(0, 10)" :key="i" class="list-item">
            <view class="item-time">
              <text class="time-label">{{ formatDate(item.timestamp) }}</text>
              <text class="time-value">{{ formatTime(item.timestamp) }}</text>
            </view>
            <view class="item-data">
              <view class="data-row">
                <text class="data-label">运动次数</text>
                <text class="data-value">{{ item.motion_5min_sum }}</text>
              </view>
              <view class="data-row">
                <text class="data-label">z-score</text>
                <text class="data-value" :class="{ high: item.motion_zscore > 2.5 }">{{ item.motion_zscore.toFixed(2) }}</text>
              </view>
              <view class="data-row">
                <text class="data-label">活动指数</text>
                <text class="data-value">{{ item.activity_index.toFixed(2) }}</text>
              </view>
              <view class="data-row" v-if="item.sht30_temp_raw">
                <text class="data-label">温度</text>
                <text class="data-value">{{ item.sht30_temp_raw.toFixed(1) }}°C</text>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 模块4：每日异常汇总表 -->
      <view class="chart-card summary-card">
        <view class="card-header">
          <text class="card-title">每日异常汇总</text>
        </view>
        <view class="summary-body">
          <view class="summary-row header">
            <text class="summary-cell">日期</text>
            <text class="summary-cell">异常点数</text>
            <text class="summary-cell">最高z-score</text>
            <text class="summary-cell">状态</text>
          </view>
          <view v-for="(item, i) in dailySummary" :key="i" class="summary-row">
            <text class="summary-cell">{{ item.date }}</text>
            <text class="summary-cell" :class="{ highlight: item.count > 0 }">{{ item.count }}</text>
            <text class="summary-cell">{{ item.maxZscore.toFixed(2) }}</text>
            <text class="summary-cell">
              <text :class="item.isAnomalous ? 'anomalous' : 'normal'">{{ item.isAnomalous ? '🔴异常' : '🟢正常' }}</text>
            </text>
          </view>
        </view>
      </view>

      <!-- 模块5：预警规则说明 -->
      <view class="chart-card rules-card">
        <view class="card-header">
          <text class="card-title">预警规则说明</text>
        </view>
        <view class="rules-body">
          <view class="rule-item">
            <text class="rule-label">检测时段</text>
            <text class="rule-value">22:00 ~ 06:00（夜间）</text>
          </view>
          <view class="rule-item">
            <text class="rule-label">统计窗口</text>
            <text class="rule-value">5分钟（motion_5min_sum）</text>
          </view>
          <view class="rule-item">
            <text class="rule-label">异常阈值</text>
            <text class="rule-value highlight">z-score > 2.5</text>
          </view>
          <view class="rule-item">
            <text class="rule-label">判定逻辑</text>
            <text class="rule-value">单点 z-score 超过阈值即标记异常</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const statusBarHeight = ref(44)
const dateRange = ref('近3天')
const rawData = ref([])
const filteredData = ref([])
const tooltipVisible = ref(false)
const tooltipData = ref(null)
const tooltipPosition = ref({ x: 0, y: 0 })

async function loadData() {
  try {
    const res = await fetch('/api/v1/analysis/night-anomaly?days=3').then(r => r.json()).catch(() => null)
    if (res && res.code === 200 && res.data && res.data.points && res.data.points.length) {
      rawData.value = res.data.points.map(row => ({
        timestamp: new Date(row.timestamp),
        date: row.date,
        hour: row.hour || 0,
        minute_of_day: row.minute_of_day || 0,
        is_night: row.is_night || 0,
        pir_gpio: row.pir_gpio,
        motion_5min_sum: row.motion_5min_sum || 0,
        motion_30min_sum: row.motion_30min_sum || 0,
        activity_index: row.activity_index || 0,
        activity_10min_mean: row.activity_10min_mean || 0,
        temp_comfort: row.temp_comfort || 0,
        humi_comfort: row.humi_comfort || 0,
        env_discomfort: row.env_discomfort || 0,
        motion_zscore: row.motion_zscore || 0,
        is_anomaly_point: row.is_anomaly_point || 0,
        sht30_temp_raw: row.sht30_temp_raw
      }))
      filteredData.value = rawData.value.filter(d => d.is_night === 1)
    } else {
      useFallbackData()
    }
  } catch (e) {
    console.error('数据加载失败', e)
    useFallbackData()
  }
}

function useFallbackData() {
  const now = new Date()
  const data = []
  for (let i = 480; i >= 0; i--) {
    const ts = new Date(now.getTime() - i * 15 * 1000)
    const isNight = ts.getHours() >= 22 || ts.getHours() < 6
    const baseMotion = isNight ? 0.2 : 1.5
    const noise = Math.random() * 0.5
    const motion = baseMotion + noise
    const zscore = (motion - baseMotion) * 2
    const isAnomaly = zscore > 2.5 && Math.random() > 0.7
    data.push({
      timestamp: ts,
      date: ts.toISOString().split('T')[0],
      hour: ts.getHours(),
      minute_of_day: ts.getHours() * 60 + ts.getMinutes(),
      is_night: isNight ? 1 : 0,
      pir_gpio: Math.random() > 0.9 ? 1 : 0,
      motion_5min_sum: motion,
      motion_30min_sum: motion * 6,
      activity_index: motion * 10,
      activity_10min_mean: motion * 5,
      temp_comfort: Math.random() > 0.3 ? 1 : 0,
      humi_comfort: Math.random() > 0.3 ? 1 : 0,
      env_discomfort: Math.random() * 2,
      motion_zscore: zscore,
      is_anomaly_point: isAnomaly ? 1 : 0,
      sht30_temp_raw: 26 + Math.random() * 6
    })
  }
  rawData.value = data
  filteredData.value = data.filter(d => d.is_night === 1)
}

function goBack() {
  uni.navigateBack()
}

const todayData = computed(() => {
  if (!filteredData.value.length) return []
  const today = new Date().toISOString().split('T')[0]
  return filteredData.value.filter(d => d.date === today)
})

const todayIsAnomalous = computed(() => todayData.value.some(d => d.is_anomaly_point === 1))
const todayAnomalyCount = computed(() => todayData.value.filter(d => d.is_anomaly_point === 1).length)
const todayMaxZscore = computed(() => {
  if (!todayData.value.length) return 0
  return Math.max(...todayData.value.map(d => d.motion_zscore))
})

const latestTime = computed(() => {
  if (!filteredData.value.length) return '--:--'
  const latest = filteredData.value[filteredData.value.length - 1]
  return formatTime(latest.timestamp)
})

const chartData = computed(() => filteredData.value)

const motionLinePoints = computed(() => {
  const data = chartData.value
  if (!data.length) return ''
  const max = Math.max(...data.map(d => d.motion_5min_sum), 1)
  const min = Math.min(...data.map(d => d.motion_5min_sum), 0)
  const range = max - min || 1
  return data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100
    const y = 60 - ((d.motion_5min_sum - min) / range) * 55
    return `${x},${Math.max(5, Math.min(55, y))}`
  }).join(' ')
})

const thresholdY = computed(() => {
  const data = chartData.value
  if (!data.length) return 30
  const values = data.map(d => d.motion_5min_sum)
  const mean = values.reduce((a, b) => a + b, 0) / values.length
  const std = Math.sqrt(values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length)
  const threshold = mean + 2.5 * std
  const max = Math.max(...values, threshold, 1)
  const min = Math.min(...values, 0)
  const range = max - min || 1
  return Math.max(5, Math.min(55, 60 - ((threshold - min) / range) * 55))
})

const anomalyPoints = computed(() => {
  const data = chartData.value
  if (!data.length) return []
  const max = Math.max(...data.map(d => d.motion_5min_sum), 1)
  const min = Math.min(...data.map(d => d.motion_5min_sum), 0)
  const range = max - min || 1
  const result = []
  data.forEach((d, idx) => {
    if (d.is_anomaly_point === 1) {
      const x = (idx / (data.length - 1)) * 100
      const y = 60 - ((d.motion_5min_sum - min) / range) * 55
      result.push({ x, y: Math.max(5, Math.min(55, y)) })
    }
  })
  return result
})

const xLabels = computed(() => {
  const data = chartData.value
  if (!data.length) return []
  const step = Math.floor(data.length / 5)
  return data.filter((_, i) => i % step === 0 || i === data.length - 1).map(d => formatTime(d.timestamp))
})

const xLabelPositions = computed(() => {
  const data = chartData.value
  if (!data.length) return []
  const step = Math.floor(data.length / 5)
  const indices = []
  for (let i = 0; i < data.length; i += step) {
    indices.push(i)
  }
  if (indices[indices.length - 1] !== data.length - 1) {
    indices.push(data.length - 1)
  }
  return indices.map(i => (i / (data.length - 1)) * 100)
})

const leftYLabels = computed(() => {
  const data = chartData.value
  if (!data.length) return []
  const values = data.map(d => d.motion_5min_sum)
  const max = Math.max(...values, 1)
  const min = Math.min(...values, 0)
  const range = max - min || 1
  const labels = []
  for (let i = 0; i <= 4; i++) {
    labels.push((min + range * (i / 4)).toFixed(1))
  }
  return labels
})

const rightYLabels = computed(() => {
  const data = chartData.value
  if (!data.length) return []
  const zscores = data.map(d => d.motion_zscore)
  const max = Math.max(...zscores, 5)
  const min = Math.min(...zscores, -5)
  const range = max - min || 1
  const labels = []
  for (let i = 0; i <= 4; i++) {
    labels.push((min + range * (i / 4)).toFixed(1))
  }
  return labels
})

const zscoreLinePoints = computed(() => {
  const data = chartData.value
  if (!data.length) return ''
  const zscores = data.map(d => d.motion_zscore)
  const max = Math.max(...zscores, 5)
  const min = Math.min(...zscores, -5)
  const range = max - min || 1
  return data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100
    const y = 60 - ((d.motion_zscore - min) / range) * 55
    return `${x},${Math.max(5, Math.min(55, y))}`
  }).join(' ')
})

const clickablePoints = computed(() => {
  const data = chartData.value
  if (!data.length) return []
  const max = Math.max(...data.map(d => d.motion_5min_sum), 1)
  const min = Math.min(...data.map(d => d.motion_5min_sum), 0)
  const range = max - min || 1
  return data.map((d, i) => {
    const x = (i / (data.length - 1)) * 100
    const y = 60 - ((d.motion_5min_sum - min) / range) * 55
    return { x, y: Math.max(5, Math.min(55, y)) }
  })
})

const anomalyList = computed(() => filteredData.value.filter(d => d.is_anomaly_point === 1).reverse())

const dailySummary = computed(() => {
  const grouped = {}
  filteredData.value.forEach(d => {
    if (!grouped[d.date]) {
      grouped[d.date] = { count: 0, maxZscore: 0, isAnomalous: false }
    }
    if (d.is_anomaly_point === 1) grouped[d.date].count++
    if (d.motion_zscore > grouped[d.date].maxZscore) grouped[d.date].maxZscore = d.motion_zscore
    if (d.is_anomaly_point === 1) grouped[d.date].isAnomalous = true
  })
  return Object.entries(grouped).map(([date, info]) => ({
    date: date.slice(5),
    count: info.count,
    maxZscore: info.maxZscore,
    isAnomalous: info.isAnomalous
  })).slice(-7).reverse()
})

function formatDate(date) {
  const d = new Date(date)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function formatTime(date) {
  const d = new Date(date)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
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

function filterDataByRange(index) {
  if (!rawData.value.length) return
  const now = new Date()
  const startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  let startTime = startOfDay
  switch (index) {
    case 0: startTime = startOfDay; break
    case 1: startTime = new Date(startOfDay.getTime() - 2 * 24 * 60 * 60 * 1000); break
    case 2: const dayOfWeek = now.getDay(); const diff = dayOfWeek === 0 ? 6 : dayOfWeek - 1; startTime = new Date(startOfDay.getTime() - diff * 24 * 60 * 60 * 1000); break
    case 3: startTime = new Date(now.getFullYear(), now.getMonth(), 1); break
  }
  filteredData.value = rawData.value.filter(d => d.timestamp >= startTime && d.timestamp <= now && d.is_night === 1)
  uni.showToast({ title: `已切换到${dateRange.value}`, icon: 'success' })
}

function handlePointClick(idx, e) {
  const data = chartData.value
  if (!data.length || idx < 0 || idx >= data.length) return
  const item = data[idx]
  tooltipData.value = item

  let clientX = 0, clientY = 0
  if (e.clientX !== undefined) { clientX = e.clientX; clientY = e.clientY }
  else if (e.touches && e.touches[0]) { clientX = e.touches[0].clientX; clientY = e.touches[0].clientY }
  else if (e.changedTouches && e.changedTouches[0]) { clientX = e.changedTouches[0].clientX; clientY = e.changedTouches[0].clientY }

  const chartArea = document.querySelector('.chart-area')
  if (chartArea) {
    const rect = chartArea.getBoundingClientRect()
    const x = clientX - rect.left
    const y = clientY - rect.top
    tooltipPosition.value = { x, y }
  } else {
    tooltipPosition.value = { x: clientX, y: clientY }
  }
  tooltipVisible.value = true
}

function handleChartAreaClick() {
  tooltipVisible.value = false
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  padding: 0 16rpx 120rpx;
}

// 桌面端：避开侧边栏
@include desktop {
  .page {
    margin-left: $sidebar-width;
    padding: 0 20px 40px;
    max-width: calc(#{$content-max-width} - #{$sidebar-width});
  }
}

@include desktop-lg {
  .page {
    margin-left: $sidebar-width-lg;
    max-width: calc(#{$content-max-width-lg} - #{$sidebar-width-lg});
  }
}

.status-bar { background: rgba(15, 23, 42, 0.98); }

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
}

.logo { display: flex; align-items: center; gap: 10rpx; }
.logo-icon { font-size: 32rpx; }
.app-name { font-size: 28rpx; font-weight: bold; color: #fff; }

.back-btn {
  background: rgba(255, 255, 255, 0.08);
  padding: 8rpx 16rpx;
  border-radius: 14rpx;
  font-size: 22rpx;
  color: #94a3b8;
}

.header-actions { display: flex; align-items: center; gap: 10rpx; }

.date-range {
  display: flex; align-items: center; gap: 6rpx;
  background: rgba(255, 255, 255, 0.1);
  padding: 8rpx 16rpx; border-radius: 16rpx;
}
.date-text { font-size: 22rpx; color: #fff; }
.date-arrow { font-size: 16rpx; color: #94a3b8; }

.main-content { margin-top: 12rpx; display: flex; flex-direction: column; gap: 10rpx; }

.chart-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 14rpx; padding: 16rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.05);
}

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.card-title { font-size: 24rpx; font-weight: bold; color: #fff; }
.card-subtitle { font-size: 18rpx; color: #64748b; }

.legend { display: flex; gap: 12rpx; }
.legend-item { display: flex; align-items: center; gap: 6rpx; font-size: 18rpx; color: #94a3b8; }
.legend-item .line { width: 20rpx; height: 3rpx; border-radius: 2rpx; }
.legend-item .dot { width: 10rpx; height: 10rpx; border-radius: 50%; }

.status-cards { display: flex; gap: 10rpx; }
.status-card {
  flex: 1; min-width: 110rpx;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 14rpx; padding: 14rpx 10rpx;
  display: flex; flex-direction: column; align-items: center; gap: 6rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.05);
  &.anomaly { border-color: rgba(239, 68, 68, 0.4); background: rgba(239, 68, 68, 0.1); }
  &.count { border-color: rgba(239, 68, 68, 0.3); }
  &.zscore { border-color: rgba(245, 158, 11, 0.3); }
}

.card-icon { font-size: 28rpx; }
.card-info { display: flex; flex-direction: column; align-items: center; gap: 2rpx; }
.card-value { font-size: 22rpx; font-weight: bold; color: #fff; }
.card-label { font-size: 18rpx; color: #94a3b8; }

.chart-body { position: relative; height: 180rpx; display: flex; align-items: flex-start; }
.chart-area { position: relative; flex: 1; height: 150rpx; }

.axis-left { position: relative; width: 48rpx; height: 150rpx; flex-shrink: 0; }
.axis-left .axis-label-left { position: absolute; font-size: 14rpx; color: #64748b; text-align: right; padding-right: 6rpx; transform: translateY(50%); }

.axis-right { position: relative; width: 48rpx; height: 150rpx; flex-shrink: 0; }
.axis-right .axis-label-right { position: absolute; font-size: 14rpx; color: #64748b; text-align: left; padding-left: 6rpx; transform: translateY(50%); }

.chart-svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.clickable-point { cursor: pointer; }

.chart-tooltip {
  position: absolute;
  background: rgba(15, 23, 42, 0.95);
  border: 1rpx solid rgba(255, 255, 255, 0.1);
  border-radius: 10rpx; padding: 12rpx;
  z-index: 100; min-width: 180rpx;
  transform: translate(-50%, -100%) translateY(-8rpx);
  box-shadow: 0 6rpx 24rpx rgba(0, 0, 0, 0.4);
}
.chart-tooltip::after {
  content: ''; position: absolute; bottom: -6rpx; left: 50%;
  transform: translateX(-50%);
  border-left: 6rpx solid transparent; border-right: 6rpx solid transparent;
  border-top: 6rpx solid rgba(255, 255, 255, 0.1);
}

.tooltip-header { font-size: 22rpx; font-weight: bold; color: #fff; margin-bottom: 8rpx; padding-bottom: 6rpx; border-bottom: 1rpx solid rgba(255, 255, 255, 0.1); }
.tooltip-row { display: flex; justify-content: space-between; align-items: center; gap: 12rpx; margin-bottom: 6rpx; }
.tooltip-label { font-size: 20rpx; color: #94a3b8; }
.tooltip-value { font-size: 20rpx; color: #cbd5e1; font-weight: bold; }
.tooltip-value.high { color: #ef4444; }

.axis-bottom { position: absolute; bottom: 0; left: 48rpx; right: 48rpx; height: 30rpx; }
.axis-bottom .axis-label { position: absolute; transform: translateX(-50%); font-size: 16rpx; color: #64748b; }

.list-scroll { max-height: 300rpx; }
.list-item { display: flex; gap: 14rpx; padding: 12rpx; background: rgba(255, 255, 255, 0.03); border-radius: 10rpx; margin-bottom: 10rpx; }
.list-item:last-child { margin-bottom: 0; }
.item-time { width: 84rpx; flex-shrink: 0; display: flex; flex-direction: column; gap: 2rpx; }
.time-label { font-size: 16rpx; color: #64748b; }
.time-value { font-size: 22rpx; font-weight: bold; color: #fff; }
.item-data { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.data-row { display: flex; justify-content: space-between; align-items: center; }
.data-label { font-size: 20rpx; color: #94a3b8; }
.data-value { font-size: 20rpx; color: #cbd5e1; }
.data-value.high { color: #ef4444; font-weight: bold; }

.summary-body { display: flex; flex-direction: column; }
.summary-row { display: flex; border-bottom: 1rpx solid rgba(255, 255, 255, 0.05); }
.summary-row:last-child { border-bottom: none; }
.summary-row.header { background: rgba(255, 255, 255, 0.05); }
.summary-cell {
  flex: 1; padding: 12rpx 6rpx; font-size: 20rpx; text-align: center; color: #cbd5e1;
  &.highlight { color: #ef4444; font-weight: bold; }
  .anomalous { color: #ef4444; }
  .normal { color: #22c55e; }
}
.summary-row.header .summary-cell { font-weight: bold; color: #94a3b8; }

.rules-body { display: flex; flex-direction: column; gap: 12rpx; }
.rule-item { display: flex; justify-content: space-between; align-items: center; padding: 10rpx 14rpx; background: rgba(255, 255, 255, 0.03); border-radius: 10rpx; }
.rule-label { font-size: 22rpx; color: #94a3b8; }
.rule-value { font-size: 22rpx; color: #cbd5e1; }
.rule-value.highlight { color: #ef4444; font-weight: bold; }
</style>
