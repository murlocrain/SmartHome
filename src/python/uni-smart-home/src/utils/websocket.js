// WebSocket 连接管理工具
import { createWebSocket, createSceneWebSocket } from '@/api'

class WebSocketManager {
  constructor() {
    this.ws = null
    this.sceneWs = null
    this.heartbeatTimer = null
    this.reconnectTimer = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000
    this.familyId = null
    this.onMessageCallback = null
    this.onSceneMessageCallback = null
  }

  // 连接网关WebSocket
  connect(familyId) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket已连接')
      return
    }

    this.familyId = familyId
    this.ws = createWebSocket(familyId)

    this.ws.onopen = () => {
      console.log('WebSocket连接成功')
      this.reconnectAttempts = 0
      this.startHeartbeat()
    }

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('收到WebSocket消息:', message)

      if (message.type === 'pong') {
        // 心跳响应
        return
      }

      if (this.onMessageCallback) {
        this.onMessageCallback(message)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket错误:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket连接关闭')
      this.stopHeartbeat()
      this.handleReconnect()
    }
  }

  // 连接场景服务WebSocket
  connectScene(familyId) {
    if (this.sceneWs && this.sceneWs.readyState === WebSocket.OPEN) {
      console.log('场景WebSocket已连接')
      return
    }

    this.sceneWs = createSceneWebSocket(familyId)

    this.sceneWs.onopen = () => {
      console.log('场景WebSocket连接成功')
    }

    this.sceneWs.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('收到场景WebSocket消息:', message)

      if (this.onSceneMessageCallback) {
        this.onSceneMessageCallback(message)
      }
    }

    this.sceneWs.onerror = (error) => {
      console.error('场景WebSocket错误:', error)
    }

    this.sceneWs.onclose = () => {
      console.log('场景WebSocket连接关闭')
    }
  }

  // 发送消息
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket未连接，无法发送消息')
    }
  }

  // 发送设备控制命令
  sendDeviceCommand(deviceId, command) {
    this.send({
      device_id: deviceId,
      command: command
    })
  }

  // 发送心跳
  sendHeartbeat() {
    this.send({ type: 'ping' })
  }

  // 开始心跳检测
  startHeartbeat() {
    this.heartbeatTimer = setInterval(() => {
      this.sendHeartbeat()
    }, 30000) // 每30秒发送一次心跳
  }

  // 停止心跳检测
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // 处理重连
  handleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('达到最大重连次数，停止重连')
      return
    }

    this.reconnectAttempts++
    console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)

    this.reconnectTimer = setTimeout(() => {
      this.connect(this.familyId)
    }, this.reconnectDelay)
  }

  // 设置消息回调
  onMessage(callback) {
    this.onMessageCallback = callback
  }

  // 设置场景消息回调
  onSceneMessage(callback) {
    this.onSceneMessageCallback = callback
  }

  // 断开连接
  disconnect() {
    this.stopHeartbeat()

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }

    if (this.sceneWs) {
      this.sceneWs.close()
      this.sceneWs = null
    }

    this.reconnectAttempts = 0
  }

  // 获取连接状态
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }

  // 获取场景连接状态
  isSceneConnected() {
    return this.sceneWs && this.sceneWs.readyState === WebSocket.OPEN
  }
}

// 创建单例实例
const wsManager = new WebSocketManager()

export default wsManager
