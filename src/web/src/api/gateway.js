// 网关服务相关API（不经过 /api/v1 前缀）

// 获取连接状态
export const getConnectionStatus = () => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: '/connections',
      method: 'GET',
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else reject(res)
      },
      fail: reject
    })
  })
}

// 健康检查
export const healthCheck = () => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: '/health',
      method: 'GET',
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else reject(res)
      },
      fail: reject
    })
  })
}

// 就绪检查
export const readyCheck = () => {
  return new Promise((resolve, reject) => {
    uni.request({
      url: '/ready',
      method: 'GET',
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data)
        else reject(res)
      },
      fail: reject
    })
  })
}

// 创建WebSocket连接（网关服务，携带token认证）
export const createWebSocket = (familyId) => {
  const token = uni.getStorageSync('token')
  const wsUrl = `ws://${window.location.host}/ws/${familyId}?token=${encodeURIComponent(token || '')}`
  return new WebSocket(wsUrl)
}

// 创建场景服务WebSocket连接（携带token认证）
export const createSceneWebSocket = (familyId) => {
  const token = uni.getStorageSync('token')
  const wsUrl = `ws://localhost:8014/api/v1/scenes/ws/${familyId}?token=${encodeURIComponent(token || '')}`
  return new WebSocket(wsUrl)
}
