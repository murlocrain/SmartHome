<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/user'
import { startMonitoring } from '@/composables/useNetwork.js'
import { useBreakpoint, initBreakpoint } from '@/composables/useBreakpoint.js'

// Initialize device detection (singleton, called before any component render)
initBreakpoint()

// Watch device category changes & sync to <html> attribute for CSS selector support
const { deviceCategory, isDesktop } = useBreakpoint()

// Sync device class to <html> element on every change (CSS won't flicker because
// `@include desktop` media-queries don't depend on this class — it's for JS logic)
import { watch } from 'vue'
watch([deviceCategory, isDesktop], () => {
  if (typeof document !== 'undefined') {
    const cls = isDesktop.value ? 'desktop' : 'mobile'
    document.documentElement.className = cls
    document.documentElement.setAttribute('data-device', deviceCategory.value)
  }
})

onLaunch(() => {
  console.log('App Launch')

  // 启动网络状态监听
  startMonitoring()

  // 检查用户登录状态
  const userStore = useUserStore()
  const token = uni.getStorageSync('token')

  if (!token) {
    // 没有token，跳转到登录页
    uni.reLaunch({ url: '/pages/login/index' })
  } else {
    // 有token，验证是否有效
    userStore.fetchUserInfo().catch(() => {
      // Token无效，已经在API层处理跳转
    })
  }
})

onShow(() => {
  console.log('App Show')
})

onHide(() => {
  console.log('App Hide')
})
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

page {
  background-color: #0f172a;
}

// 桌面端全局样式
@include desktop {
  page {
    background-color: #0a0f1a;
  }

  // uni-app 的 page 容器
  uni-page-body {
    min-height: 100vh;
  }
}

// 大屏桌面全局样式
@include desktop-lg {
  page {
    font-size: 15px;
  }
}

// 超大屏桌面全局样式
@include desktop-xl {
  page {
    font-size: 16px;
  }
}

// 全局滚动条样式（桌面端）
@include desktop {
  ::-webkit-scrollbar {
    width: 6px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 3px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.25);
  }
}
</style>
