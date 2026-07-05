import request from './index'

// ========== AI 聊天 ==========
export const aiChat = (message) => {
  return request({
    url: '/agent/chat',
    method: 'POST',
    data: { message },
  })
}

// ========== AI 智能控制 ==========
export const aiAgentControl = (message) => {
  return request({
    url: '/agent/control',
    method: 'POST',
    data: { message },
  })
}

// ========== AI 流式对话 WebSocket ==========
let ws = null
let messageHandler = null

export const connectAgentWS = (familyId, onMessage) => {
  closeAgentWS()

  const token = uni.getStorageSync('token')
  if (!token) {
    console.warn('[AgentWS] 没有 token，无法连接')
    return
  }

  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = location.host
  const url = `${protocol}//${host}/api/v1/agent/ws/${familyId}?token=${token}`

  try {
    ws = new WebSocket(url)
    ws.onopen = () => console.log('[AgentWS] 已连接')
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'pong') return
        if (onMessage) onMessage(data)
        if (messageHandler) messageHandler(data)
      } catch (err) {
        console.error('[AgentWS] 消息解析失败:', err)
      }
    }
    ws.onerror = (e) => console.error('[AgentWS] 错误:', e)
    ws.onclose = () => {
      console.log('[AgentWS] 已断开')
      ws = null
    }
  } catch (e) {
    console.error('[AgentWS] 连接失败:', e)
  }
}

export const sendAgentWSMessage = (message, mode = 'chat') => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.warn('[AgentWS] 未连接')
    return false
  }
  ws.send(JSON.stringify({ type: 'message', message, mode }))
  return true
}

export const closeAgentWS = () => {
  if (ws) {
    ws.close()
    ws = null
  }
}

export const onAgentMessage = (handler) => {
  messageHandler = handler
}
