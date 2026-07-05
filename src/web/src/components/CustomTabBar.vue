<template>
  <view
    class="tab-bar"
    :class="[
      isDesktop ? (sidebarCollapsed ? 'sidebar sidebar-collapsed' : 'sidebar') : 'bottom-bar'
    ]"
    :style="tabBarStyle"
    @mouseenter="onSidebarEnter"
    @mouseleave="onSidebarLeave"
  >
    <view v-if="isDesktop" class="sidebar-brand">
      <text class="brand-icon">🏠</text>
      <text class="brand-text" v-show="!sidebarCollapsed">智能环境监测</text>
    </view>

    <view class="tab-items" :class="{ 'sidebar-items': isDesktop }">
      <view
        v-for="(tab, index) in tabs"
        :key="tab.path"
        class="tab-item"
        :class="{ active: currentIndex === index }"
        @tap="switchTab(index)"
        :title="isDesktop && sidebarCollapsed ? tab.name : ''"
      >
        <text class="tab-icon">{{ tab.icon }}</text>
        <text class="tab-text" v-show="!isDesktop || !sidebarCollapsed">{{ tab.name }}</text>
      </view>
    </view>

    <view v-if="isDesktop" class="sidebar-footer">
      <view class="sidebar-collapse-btn" @tap.stop="toggleSidebar">
        <text class="collapse-icon">{{ sidebarCollapsed ? '▶' : '◀' }}</text>
      </view>
      <text class="sidebar-name" v-show="!sidebarCollapsed">v2.0</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { themeStore } from '@/store/theme.js'
import { useBreakpoint } from '@/composables/useBreakpoint.js'

const props = defineProps({
  currentIndex: { type: Number, default: 0 }
})

const tabs = [
  { name: '首页', icon: '📊', path: '/pages/index/index' },
  { name: '灯光', icon: '💡', path: '/pages/devices/index' },
  { name: '电机', icon: '⚙️', path: '/pages/scenes/index' },
  { name: '设备', icon: '📡', path: '/pages/profile/index' },
  { name: '分析', icon: '📈', path: '/pages/data-analysis/index' },
]

const { isDesktop } = useBreakpoint()

const sidebarCollapsed = ref(true)
let collapseTimer = null

function onSidebarEnter() {
  clearTimeout(collapseTimer)
  sidebarCollapsed.value = false
}

function onSidebarLeave() {
  collapseTimer = setTimeout(() => {
    sidebarCollapsed.value = true
  }, 600)
}

function toggleSidebar() {
  clearTimeout(collapseTimer)
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const tabBarStyle = computed(() => {
  const t = themeStore.getCurrentTheme()
  return isDesktop.value
    ? { background: t.sidebarColor || t.cardColor }
    : { background: t.cardColor }
})

const switchTab = (index) => {
  uni.switchTab({ url: tabs[index].path })
}
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.tab-bar {
  display: flex;
}

// ========== 移动端：底部导航 ==========
.tab-bar.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 120rpx;
  padding-bottom: env(safe-area-inset-bottom);
  flex-direction: row;
  justify-content: space-around;
  align-items: center;
  border-top: 1rpx solid rgba(255, 255, 255, 0.06);
  z-index: 999;
}

.tab-items {
  display: flex;
  flex-direction: row;
  width: 100%;
  justify-content: space-around;
  align-items: center;
  height: 100%;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  height: 100%;
  gap: 6rpx;
  transition: all 0.2s ease;
}

.tab-icon {
  font-size: 40rpx;
  transition: transform 0.2s;
}

.tab-text {
  font-size: 22rpx;
  color: #94a3b8;
  transition: color 0.2s;
}

.tab-item.active .tab-text {
  color: #818cf8;
  font-weight: 600;
}

.tab-item.active .tab-icon {
  transform: scale(1.1);
}

// ========== 桌面端：左侧侧边栏 ==========
@include desktop {
  .tab-bar.sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: $sidebar-width;
    flex-direction: column;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    z-index: 100;
    transition: width 0.25s ease;
    overflow: hidden;
  }

  .tab-bar.sidebar.sidebar-collapsed {
    width: 56px;
  }

  .sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 28px 24px 24px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    white-space: nowrap;
  }

  .sidebar-collapsed .sidebar-brand {
    padding: 28px 16px 24px;
    justify-content: center;
  }

  .brand-icon {
    font-size: 26px;
    flex-shrink: 0;
  }

  .brand-text {
    font-size: 16px;
    font-weight: bold;
    color: #fff;
  }

  .tab-items.sidebar-items {
    flex-direction: column;
    justify-content: flex-start;
    align-items: stretch;
    padding: 16px 16px;
    gap: 6px;
    flex: 1;
    width: auto;
  }

  .sidebar-collapsed .tab-items.sidebar-items {
    padding: 16px 10px;
  }

  .tab-item {
    flex-direction: row;
    gap: 14px;
    padding: 13px 18px;
    border-radius: 12px;
    cursor: pointer;
    height: auto;
    transition: all 0.2s ease;
    white-space: nowrap;

    &:hover {
      background: rgba(255, 255, 255, 0.05);
    }
  }

  .sidebar-collapsed .tab-item {
    gap: 0;
    padding: 13px 0;
    justify-content: center;
    border-radius: 10px;
  }

  .tab-icon {
    font-size: 22px;
    flex-shrink: 0;
  }

  .tab-text {
    font-size: 14px;
    color: #94a3b8;
  }

  .tab-item.active {
    background: rgba(129, 140, 248, 0.12);
  }

  .tab-item.active .tab-text {
    color: #818cf8;
    font-weight: 600;
  }

  .sidebar-footer {
    padding: 16px 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .sidebar-collapsed .sidebar-footer {
    flex-direction: column-reverse;
    gap: 8px;
    padding: 12px 10px;
  }

  .sidebar-collapse-btn {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
    }
  }

  .collapse-icon {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.35);
  }

  .sidebar-name {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.3);
    white-space: nowrap;
  }
}

// ========== 大屏：侧边栏更宽 ==========
@include desktop-lg {
  .tab-bar.sidebar {
    width: $sidebar-width-lg;
  }

  .tab-bar.sidebar.sidebar-collapsed {
    width: 56px;
  }

  .sidebar-brand {
    padding: 32px 28px 28px;
  }

  .sidebar-collapsed .sidebar-brand {
    padding: 32px 16px 28px;
    justify-content: center;
  }

  .brand-icon { font-size: 30px; }
  .brand-text { font-size: 18px; }

  .tab-items.sidebar-items {
    padding: 0 20px;
    gap: 10px;
  }

  .sidebar-collapsed .tab-items.sidebar-items {
    padding: 0 10px;
  }

  .tab-item {
    padding: 15px 20px;
    border-radius: 14px;
  }

  .sidebar-collapsed .tab-item {
    padding: 15px 0;
    justify-content: center;
  }

  .tab-icon { font-size: 26px; }
  .tab-text { font-size: 15px; }
}
</style>
