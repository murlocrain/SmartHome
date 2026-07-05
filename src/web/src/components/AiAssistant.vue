<template>
  <!-- 浮动入口按钮 -->
  <view class="ai-fab" v-if="!visible" @tap="open" :style="{ background: theme.primaryColor }">
    <text class="fab-icon">🤖</text>
  </view>

  <!-- 聊天面板 -->
  <view class="ai-overlay" v-if="visible" @tap.self="close">
    <view class="ai-panel" :style="{ background: theme.cardColor }">
      <!-- 头部 -->
      <view class="ai-header" :style="{ borderBottom: '1px solid ' + theme.bgColor }">
        <view class="ai-header-left">
          <text class="ai-avatar">🤖</text>
          <view>
            <text class="ai-title" :style="{ color: theme.textColor }">DeepSeek 助手</text>
            <text class="ai-subtitle" :style="{ color: theme.textMuted }">语音/文字控制智能家居</text>
          </view>
        </view>
        <view class="ai-close" @tap="close" :style="{ color: theme.textSecondary }">
          <text>✕</text>
        </view>
      </view>

      <!-- 消息列表 -->
      <scroll-view class="ai-messages" scroll-y :scroll-into-view="scrollTarget">
        <view v-if="messages.length === 0" class="ai-welcome" :style="{ color: theme.textMuted }">
          <text class="welcome-icon">🏠</text>
          <text>你好！我是你的智能家居助手。</text>
          <text>试试对我说：</text>
        </view>
        <view class="ai-hints" v-if="messages.length === 0">
          <view class="hint-item" :style="{ background: theme.bgColor, color: theme.textColor }" @tap="sendHint('打开灯光')">" 打开灯光 "</view>
          <view class="hint-item" :style="{ background: theme.bgColor, color: theme.textColor }" @tap="sendHint('打开风扇')">" 打开风扇 "</view>
          <view class="hint-item" :style="{ background: theme.bgColor, color: theme.textColor }" @tap="sendHint('现在的温度和湿度是多少？')">" 环境怎么样？"</view>
          <view class="hint-item" :style="{ background: theme.bgColor, color: theme.textColor }" @tap="sendHint('关闭所有设备')">" 关闭所有设备 "</view>
        </view>

        <view
          v-for="(msg, idx) in messages"
          :key="idx"
          :id="'msg-' + idx"
          class="msg-row"
          :class="msg.role === 'user' ? 'msg-user' : 'msg-ai'"
        >
          <view class="msg-bubble" :style="{
            background: msg.role === 'user' ? theme.primaryColor : theme.bgColor,
            color: msg.role === 'user' ? '#fff' : theme.textColor
          }">
            <text class="msg-text">{{ msg.content }}</text>
          </view>
          <view class="msg-meta" v-if="msg.deviceResult" :style="{ color: theme.textMuted }">
            <text>{{ msg.deviceResult === 'ok' ? '执行成功' : '执行失败' }}</text>
          </view>
        </view>

        <!-- 加载中 -->
        <view v-if="loading" class="msg-row msg-ai">
          <view class="msg-bubble typing" :style="{ background: theme.bgColor, color: theme.textMuted }">
            <text class="dot">●</text>
            <text class="dot delay-1">●</text>
            <text class="dot delay-2">●</text>
          </view>
        </view>

        <view id="msg-end"></view>
      </scroll-view>

      <!-- 输入区 -->
      <view class="ai-input" :style="{ borderTop: '1px solid ' + theme.bgColor, background: theme.cardColor }">
        <input
          class="input-field"
          :style="{ background: theme.bgColor, color: theme.textColor }"
          v-model="inputText"
          placeholder="输入指令或问题..."
          placeholder-class="ai-placeholder"
          :disabled="loading"
          confirm-type="send"
          @confirm="send"
        />
        <view
          class="send-btn"
          :style="{ background: inputText.trim() && !loading ? theme.primaryColor : theme.bgColor }"
          @tap="send"
        >
          <text :style="{ color: inputText.trim() && !loading ? '#fff' : theme.textMuted }">发送</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { themeStore } from '@/store/theme.js'
import { aiAgentControl } from '@/api/agent.js'

const theme = computed(() => themeStore.getCurrentTheme())

const visible = ref(false)
const inputText = ref('')
const loading = ref(false)
const messages = ref([])
const scrollTarget = ref('')

const open = () => { visible.value = true }
const close = () => { visible.value = false }

const scrollToBottom = async () => {
  await nextTick()
  scrollTarget.value = 'msg-end'
}

const addMessage = (role, content, extra = {}) => {
  messages.value.push({ role, content, ...extra })
  scrollToBottom()
}

const sendHint = (text) => {
  inputText.value = text
  send()
}

const send = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  inputText.value = ''
  addMessage('user', text)
  loading.value = true

  try {
    const res = await aiAgentControl(text)
    if (res && res.reply) {
      addMessage('ai', res.reply, {
        deviceResult: res.device_result ? (res.device_result.success ? 'ok' : 'fail') : null,
      })
    }
    // 如果有环境分析建议，追加显示
    if (res && res.suggestion && res.suggestion !== res.reply) {
      addMessage('ai', res.suggestion)
    }
  } catch (e) {
    addMessage('ai', '抱歉，AI 服务暂时不可用，请稍后重试。')
  } finally {
    loading.value = false
  }
}

// 键盘事件处理
const handleKeydown = (e) => {
  if (e.key === 'Escape') close()
}
</script>

<style lang="scss">
@use '@/styles/responsive.scss' as *;

.ai-fab {
  position: fixed;
  bottom: 160rpx;
  right: 32rpx;
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.3);
  z-index: 200;
  cursor: pointer;
  transition: transform 0.2s;

  &:active {
    transform: scale(0.92);
  }
}

.fab-icon {
  font-size: 48rpx;
}

.ai-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 300;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-panel {
  width: 92%;
  max-width: 700rpx;
  height: 75vh;
  max-height: calc(100vh - 160rpx);
  border-radius: 32rpx;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24rpx 32rpx;
  flex-shrink: 0;
}

.ai-header-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.ai-avatar {
  font-size: 44rpx;
}

.ai-title {
  font-size: 30rpx;
  font-weight: 600;
  display: block;
}

.ai-subtitle {
  font-size: 22rpx;
  display: block;
  margin-top: 2rpx;
}

.ai-close {
  font-size: 32rpx;
  padding: 8rpx 16rpx;
  cursor: pointer;
}

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24rpx;
}

.ai-welcome {
  text-align: center;
  padding: 40rpx 0;
  font-size: 28rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.welcome-icon {
  font-size: 60rpx;
}

.ai-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  padding: 0 0 24rpx;
  justify-content: center;
}

.hint-item {
  font-size: 24rpx;
  padding: 12rpx 24rpx;
  border-radius: 20rpx;
  cursor: pointer;
  transition: filter 0.2s;

  &:active {
    filter: brightness(0.9);
  }
}

.msg-row {
  display: flex;
  flex-direction: column;
  margin-bottom: 20rpx;
}

.msg-user {
  align-items: flex-end;
}

.msg-ai {
  align-items: flex-start;
}

.msg-bubble {
  max-width: 75%;
  padding: 16rpx 24rpx;
  border-radius: 20rpx;
  font-size: 28rpx;
  line-height: 1.5;
}

.msg-user .msg-bubble {
  border-bottom-right-radius: 6rpx;
}

.msg-ai .msg-bubble {
  border-bottom-left-radius: 6rpx;
}

.msg-meta {
  font-size: 20rpx;
  margin-top: 6rpx;
  padding: 0 8rpx;
}

.typing {
  display: flex;
  gap: 6rpx;
  padding: 20rpx 32rpx;
}

.dot {
  font-size: 20rpx;
  animation: bounce 1.2s infinite;
}

.dot.delay-1 {
  animation-delay: 0.2s;
}

.dot.delay-2 {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

.ai-input {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  flex-shrink: 0;
}

.input-field {
  flex: 1;
  height: 72rpx;
  border-radius: 36rpx;
  padding: 0 28rpx;
  font-size: 28rpx;
}

.ai-placeholder {
  font-size: 26rpx;
  color: #999;
}

.send-btn {
  height: 72rpx;
  padding: 0 28rpx;
  border-radius: 36rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  flex-shrink: 0;
  cursor: pointer;
}

// ========== 桌面端 ==========
@include desktop {
  .ai-fab {
    bottom: 40px;
    right: 40px;
    width: 60px;
    height: 60px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: transform 0.2s, box-shadow 0.2s;

    &:hover {
      transform: scale(1.08);
      box-shadow: 0 6px 28px rgba(0,0,0,0.5);
    }

    &:active {
      transform: scale(0.95);
    }
  }

  .fab-icon {
    font-size: 28px;
  }

  .ai-panel {
    max-width: 520px;
    height: 70vh;
    max-height: 660px;
    border-radius: 20px;
  }

  .ai-header {
    padding: 20px 28px;
  }

  .ai-avatar {
    font-size: 28px;
  }

  .ai-title {
    font-size: 17px;
  }

  .ai-subtitle {
    font-size: 13px;
  }

  .ai-close {
    font-size: 20px;
    padding: 6px 12px;
    border-radius: 8px;
    transition: background 0.2s;

    &:hover {
      background: rgba(255, 255, 255, 0.08);
    }
  }

  .ai-messages {
    padding: 20px;
  }

  .ai-welcome {
    font-size: 15px;
    padding: 32px 0;
  }

  .welcome-icon {
    font-size: 44px;
  }

  .hint-item {
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 16px;
    cursor: pointer;
    transition: filter 0.2s;

    &:hover {
      filter: brightness(1.1);
    }
  }

  .msg-bubble {
    font-size: 15px;
    padding: 12px 20px;
    border-radius: 14px;
  }

  .msg-meta {
    font-size: 12px;
  }

  .typing {
    padding: 14px 24px;
  }

  .dot {
    font-size: 14px;
  }

  .ai-input {
    padding: 14px 20px;
    padding-bottom: 14px;
    gap: 12px;
  }

  .input-field {
    height: 44px;
    border-radius: 22px;
    padding: 0 20px;
    font-size: 15px;
  }

  .ai-placeholder {
    font-size: 14px;
  }

  .send-btn {
    height: 44px;
    padding: 0 24px;
    border-radius: 22px;
    font-size: 15px;
    transition: opacity 0.2s;

    &:hover {
      opacity: 0.85;
    }
  }
}
</style>
