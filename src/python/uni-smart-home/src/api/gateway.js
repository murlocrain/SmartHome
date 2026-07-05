// 网关服务相关API
// 使用vite代理，代理配置在vite.config.ts中

const gatewayRequest = (options) => {
  const { url, method = 'GET', data = {}, header = {} } = options
  return new Promise((resolve, reject) => {
    uni.request({
      url: url,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else {
          reject(res)
        }
      },
      fail: (err) => {
        reject(err)
      }
    })
  })
}

// 获取连接状态
export const getConnectionStatus = () => {
  return gatewayRequest({
    url: '/connections',
    method: 'GET'
  })
}

// 健康检查
export const healthCheck = () => {
  return gatewayRequest({
    url: '/health',
    method: 'GET'
  })
}

// 就绪检查
export const readyCheck = () => {
  return gatewayRequest({
    url: '/ready',
    method: 'GET'
  })
}

// 创建WebSocket连接
export const createWebSocket = (familyId) => {
  const token = uni.getStorageSync('token')
  // 使用相对路径，通过vite代理转发到ws://localhost:8010
  const wsUrl = `ws://${window.location.host}/ws/${familyId}?token=${token}`
  return new WebSocket(wsUrl)
}

// 创建场景服务WebSocket连接
export const createSceneWebSocket = (familyId) => {
  // 场景服务WebSocket需要直接连接到场景服务端口
  const wsUrl = `ws://localhost:8014/api/v1/scenes/ws/${familyId}`
  return new WebSocket(wsUrl)
}
