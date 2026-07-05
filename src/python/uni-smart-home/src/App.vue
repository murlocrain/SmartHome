<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/user'

onLaunch(() => {
  console.log('App Launch')
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

<style>
page { background-color: #f5f5f5; }
</style>
