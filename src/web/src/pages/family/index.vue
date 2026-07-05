<template>
  <view class="page" :style="{ background: theme.bgColor }">
    <view class="nav-bar" :style="{ background: theme.cardColor }">
      <text class="nav-title" :style="{ color: theme.textColor }">家庭管理</text>
    </view>

    <view class="page-header">
      <text class="page-title" :style="{ color: theme.textColor }">选择家庭</text>
      <text class="page-desc" :style="{ color: theme.textSecondary }">请先创建或选择一个家庭</text>
    </view>

    <view class="family-list" v-if="familyList.length > 0">
      <view
        class="family-card"
        :style="{ background: theme.cardColor }"
        v-for="family in familyList"
        :key="family.id"
        @tap="selectFamily(family)"
      >
        <view class="family-icon">🏠</view>
        <view class="family-info">
          <text class="family-name" :style="{ color: theme.textColor }">{{ family.name }}</text>
          <text class="family-desc" :style="{ color: theme.textSecondary }">创建于 {{ formatDate(family.created_at) }}</text>
        </view>
        <view class="family-arrow" :style="{ color: theme.textSecondary }">›</view>
      </view>
    </view>

    <view class="empty-state" v-else :style="{ background: theme.cardColor }">
      <text class="empty-icon">🏠</text>
      <text class="empty-text" :style="{ color: theme.textSecondary }">还没有创建家庭</text>
      <text class="empty-desc" :style="{ color: theme.textMuted }">点击下方按钮创建您的第一个家庭</text>
    </view>

    <view class="create-section">
      <view class="input-group" :style="{ background: theme.cardColor }">
        <view class="input-label" :style="{ color: theme.textSecondary }">家庭名称</view>
        <input
          class="input-field"
          :style="{ background: theme.bgColor, color: theme.textColor }"
          type="text"
          placeholder="请输入家庭名称"
          placeholder-class="placeholder"
          v-model="newFamilyName"
        />
      </view>

      <button
        class="create-btn"
        :style="{ background: theme.primaryColor }"
        @tap="createFamily"
        :disabled="loading || !newFamilyName"
      >
        <text class="create-text" :style="{ color: '#fff' }">
          {{ loading ? '创建中...' : '创建家庭' }}
        </text>
      </button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { createFamily as createFamilyAPI, getFamilyList } from '@/api'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()
const familyList = ref([])
const newFamilyName = ref('')
const loading = ref(false)

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const loadFamilyList = async () => {
  try {
    const res = await getFamilyList()
    if (res && res.data) {
      familyList.value = res.data
      userStore.setFamilyList(res.data)
    }
  } catch (error) {
    console.error('加载家庭列表失败:', error)
    uni.showToast({ title: '加载家庭列表失败', icon: 'none' })
  }
}

const selectFamily = (family) => {
  userStore.setCurrentFamily(family)
  // 冗余写入确保数据可靠
  uni.setStorageSync('selectedFamily', {
    ...family,
    family_id: family.id,
    huawei_device_id: '6a2179727f2e6c302f77aaf8_env_monitor_01',
  })
  console.log('[DETECT:F0] family/index selectFamily → selectedFamily 已写入:', JSON.stringify(uni.getStorageSync('selectedFamily')))
  uni.showToast({ title: `已选择家庭: ${family.name}`, icon: 'success' })
  setTimeout(() => {
    uni.reLaunch({ url: '/pages/index/index' })
  }, 1500)
}

const createFamily = async () => {
  if (!newFamilyName.value || newFamilyName.value.trim().length === 0) {
    uni.showToast({ title: '请输入家庭名称', icon: 'none' })
    return
  }

  loading.value = true

  try {
    const res = await createFamilyAPI({ name: newFamilyName.value.trim() })
    if (res && res.data) {
      uni.showToast({ title: '家庭创建成功', icon: 'success' })

      // 刷新家庭列表
      await loadFamilyList()

      // 自动选择新创建的家庭
      if (familyList.value.length > 0) {
        const newFamily = familyList.value.find(f => f.name === newFamilyName.value.trim())
        if (newFamily) {
          selectFamily(newFamily)
        }
      }

      newFamilyName.value = ''
    }
  } catch (error) {
    console.error('创建家庭失败:', error)
    uni.showToast({ title: '创建家庭失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFamilyList()
})
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.page {
  min-height: 100vh;
  padding: 0 24rpx;
}

.nav-bar {
  padding: 60rpx 24rpx 20rpx;
}

.nav-title {
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

.family-list {
  margin-top: 24rpx;
}

.family-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx;
  border-radius: 20rpx;
  margin-bottom: 16rpx;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    filter: brightness(1.05);
  }
}

.family-icon {
  font-size: 48rpx;
}

.family-info {
  flex: 1;
}

.family-name {
  display: block;
  font-size: 30rpx;
  font-weight: bold;
  margin-bottom: 6rpx;
}

.family-desc {
  font-size: 24rpx;
}

.family-arrow {
  font-size: 32rpx;
}

.empty-state {
  padding: 60rpx 24rpx;
  border-radius: 20rpx;
  text-align: center;
  margin-top: 24rpx;
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

.create-section {
  margin-top: 32rpx;
}

.input-group {
  padding: 24rpx;
  border-radius: 20rpx;
  margin-bottom: 16rpx;
}

.input-label {
  font-size: 24rpx;
  margin-bottom: 12rpx;
}

.input-field {
  width: 100%;
  height: 80rpx;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 28rpx;
}

.placeholder {
  color: #94a3b8;
}

.create-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 12rpx;
  border: none;
}

.create-text {
  font-size: 32rpx;
  font-weight: 500;
}

// ========== 桌面端 ==========
@include desktop {
  .page {
    margin-left: $sidebar-width;
    padding: 32px 40px 40px;
    max-width: 700px;
    margin-right: auto;
  }

  .nav-bar {
    padding: 0 0 24px;
    background: transparent !important;
  }

  .nav-title {
    font-size: 24px;
  }

  .page-title {
    font-size: 22px;
  }

  .page-desc {
    font-size: 14px;
  }

  .family-card {
    padding: 24px 28px;
    border-radius: 14px;
    margin-bottom: 12px;
  }

  .family-icon {
    font-size: 40px;
  }

  .family-name {
    font-size: 17px;
  }

  .family-desc {
    font-size: 13px;
  }

  .family-arrow {
    font-size: 24px;
  }

  .empty-icon {
    font-size: 60px;
  }

  .empty-text {
    font-size: 17px;
  }

  .empty-desc {
    font-size: 14px;
  }

  .input-group {
    padding: 20px 24px;
    border-radius: 14px;
  }

  .input-label {
    font-size: 14px;
  }

  .input-field {
    height: 48px;
    padding: 0 16px;
    font-size: 15px;
    border-radius: 10px;
  }

  .create-btn {
    height: 48px;
    border-radius: 10px;
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.9;
    }
  }

  .create-text {
    font-size: 16px;
  }
}

// ========== 大屏桌面（1200px+） ==========
@include desktop-lg {
  .page {
    max-width: 800px;
    padding: 32px $page-padding-x-lg 44px;
  }

  .nav-title { font-size: 26px; }
  .page-title { font-size: 24px; }
  .family-name { font-size: 18px; }
  .create-text { font-size: 17px; }
}

// ========== 超大屏桌面（1440px+） ==========
@include desktop-xl {
  .page {
    margin-left: $sidebar-width-lg;
    padding: 36px $page-padding-x-lg 48px;
  }
}
</style>