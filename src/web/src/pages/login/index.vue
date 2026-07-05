<template>
  <view class="login-page" :style="{ background: theme.bgColor }">
    <view class="login-header">
      <text class="login-title" :style="{ color: theme.textColor }">数智鸿居</text>
      <text class="login-subtitle" :style="{ color: theme.textSecondary }">智能家居控制平台</text>
    </view>

    <view class="login-form" :style="{ background: theme.cardColor }">
      <view class="form-tabs">
        <view
          class="tab-item"
          :class="{ active: activeTab === 'login' }"
          :style="{ color: activeTab === 'login' ? theme.primaryColor : theme.textSecondary }"
          @tap="activeTab = 'login'"
        >
          <text>登录</text>
        </view>
        <view
          class="tab-item"
          :class="{ active: activeTab === 'register' }"
          :style="{ color: activeTab === 'register' ? theme.primaryColor : theme.textSecondary }"
          @tap="activeTab = 'register'"
        >
          <text>注册</text>
        </view>
      </view>

      <view class="form-content">
        <view class="input-group">
          <view class="input-label" :style="{ color: theme.textSecondary }">用户名</view>
          <input
            class="input-field"
            :style="{ background: theme.bgColor, color: theme.textColor }"
            type="text"
            placeholder="请输入用户名"
            placeholder-class="placeholder"
            v-model="username"
          />
        </view>

        <view class="input-group" v-if="activeTab === 'register'">
          <view class="input-label" :style="{ color: theme.textSecondary }">邮箱</view>
          <input
            class="input-field"
            :style="{ background: theme.bgColor, color: theme.textColor }"
            type="text"
            placeholder="请输入邮箱（可选）"
            placeholder-class="placeholder"
            v-model="email"
          />
        </view>

        <view class="input-group">
          <view class="input-label" :style="{ color: theme.textSecondary }">密码</view>
          <input
            class="input-field"
            :style="{ background: theme.bgColor, color: theme.textColor }"
            type="password"
            placeholder="请输入密码"
            placeholder-class="placeholder"
            v-model="password"
          />
        </view>

        <view class="input-group" v-if="activeTab === 'register'">
          <view class="input-label" :style="{ color: theme.textSecondary }">确认密码</view>
          <input
            class="input-field"
            :style="{ background: theme.bgColor, color: theme.textColor }"
            type="password"
            placeholder="请再次输入密码"
            placeholder-class="placeholder"
            v-model="confirmPassword"
          />
        </view>

        <button
          class="submit-btn"
          :style="{ background: theme.primaryColor }"
          @tap="handleSubmit"
          :disabled="loading"
        >
          <text class="submit-text" :style="{ color: '#fff' }">
            {{ loading ? '处理中...' : (activeTab === 'login' ? '登录' : '注册') }}
          </text>
        </button>
      </view>
    </view>

    <view class="login-footer">
      <text class="footer-text" :style="{ color: theme.textMuted }">
        登录即表示同意《用户协议》和《隐私政策》
      </text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { themeStore } from '@/store/theme.js'
import { useUserStore } from '@/store/user'
import { login, register } from '@/api'

const theme = computed(() => themeStore.getCurrentTheme())
const userStore = useUserStore()
const activeTab = ref('login')
const username = ref('')
const password = ref('')
const email = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const handleSubmit = async () => {
  if (!username.value || !password.value) {
    uni.showToast({ title: '请填写用户名和密码', icon: 'none' })
    return
  }

  // 用户名长度验证
  if (username.value.length < 3) {
    uni.showToast({ title: '用户名至少3个字符', icon: 'none' })
    return
  }

  if (activeTab.value === 'register') {
    // 密码长度验证
    if (password.value.length < 6) {
      uni.showToast({ title: '密码长度至少6位', icon: 'none' })
      return
    }

    // 确认密码验证
    if (password.value !== confirmPassword.value) {
      uni.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    // 邮箱格式验证（如果填写了）
    if (email.value && email.value.trim()) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email.value.trim())) {
        uni.showToast({ title: '邮箱格式不正确', icon: 'none' })
        return
      }
    }
  }

  loading.value = true

  try {
    if (activeTab.value === 'login') {
      const res = await login({
        username: username.value,
        password: password.value
      })

      if (res && res.data) {
        // 保存token到用户状态管理
        userStore.setToken(res.data.access_token, res.data.refresh_token)

        uni.showToast({ title: '登录成功', icon: 'success' })

        // 登录成功后跳转到家庭管理页面
        setTimeout(() => {
          uni.reLaunch({ url: '/pages/family/index' })
        }, 1500)
      }
    } else {
      // 构建注册数据，如果邮箱为空则不发送
      const registerData = {
        username: username.value,
        password: password.value
      }
      // 只有填写了邮箱才添加该字段
      if (email.value && email.value.trim()) {
        registerData.email = email.value.trim()
      }

      const res = await register(registerData)

      if (res && res.data) {
        uni.showToast({ title: '注册成功', icon: 'success' })

        // 注册成功后切换到登录
        setTimeout(() => {
          activeTab.value = 'login'
          confirmPassword.value = ''
          email.value = ''
        }, 1500)
      }
    }
  } catch (error) {
    console.error('操作失败:', error)
    uni.showToast({
      title: error.message || '操作失败，请重试',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 0 24rpx;
}

.login-header {
  padding: 120rpx 0 60rpx;
  text-align: center;
}

.login-title {
  display: block;
  font-size: 48rpx;
  font-weight: bold;
  margin-bottom: 16rpx;
}

.login-subtitle {
  font-size: 24rpx;
}

.login-form {
  border-radius: 24rpx;
  padding: 32rpx;
}

.form-tabs {
  display: flex;
  gap: 32rpx;
  margin-bottom: 32rpx;
}

.tab-item {
  font-size: 32rpx;
  font-weight: 500;
  padding-bottom: 8rpx;
  border-bottom: 2rpx solid transparent;

  &.active {
    border-bottom-color: currentColor;
  }
}

.form-content {
  margin-top: 24rpx;
}

.input-group {
  margin-bottom: 24rpx;
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

.submit-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 12rpx;
  margin-top: 32rpx;
  border: none;
}

.submit-text {
  font-size: 32rpx;
  font-weight: 500;
}

.login-footer {
  flex: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 32rpx 0;
}

.footer-text {
  font-size: 22rpx;
  text-align: center;
}

// ========== 桌面端：居中卡片布局 ==========
@include desktop {
  .login-page {
    align-items: center;
    justify-content: center;
    padding: 40px;
  }

  .login-header {
    padding: 0 0 40px;
  }

  .login-title {
    font-size: 32px;
  }

  .login-subtitle {
    font-size: 15px;
  }

  .login-form {
    width: 440px;
    max-width: 90vw;
    border-radius: 20px;
    padding: 40px;
  }

  .form-tabs {
    gap: 32px;
  }

  .tab-item {
    font-size: 18px;
    cursor: pointer;
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

  .submit-btn {
    height: 48px;
    border-radius: 10px;
    cursor: pointer;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.9;
    }
  }

  .submit-text {
    font-size: 16px;
  }

  .footer-text {
    font-size: 13px;
  }
}

// ========== 大屏桌面 ==========
@include desktop-lg {
  .login-form {
    width: 480px;
    padding: 48px;
  }

  .login-title {
    font-size: 36px;
  }

  .login-subtitle {
    font-size: 16px;
  }
}
</style>