// API基础配置 - 使用vite代理
// 代理配置在vite.config.ts中，转发到各后端服务
const BASE_URL = '/api/v1'

// 是否正在刷新token（防止并发请求重复刷新）
let isRefreshing = false
let refreshSubscribers = []

function onRefreshed(newToken) {
  refreshSubscribers.forEach(cb => cb(newToken))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb) {
  refreshSubscribers.push(cb)
}

// 刷新token
async function refreshAccessToken() {
  const refreshToken = uni.getStorageSync('refresh_token')
  if (!refreshToken) {
    return null
  }
  try {
    const res = await new Promise((resolve, reject) => {
      uni.request({
        url: `${BASE_URL}/auth/refresh`,
        method: 'POST',
        data: { refresh_token: refreshToken },
        header: { 'Content-Type': 'application/json' },
        success: (r) => {
          if (r.statusCode === 200) resolve(r.data)
          else reject(r)
        },
        fail: reject
      })
    })
    if (res && res.data && res.data.access_token) {
      uni.setStorageSync('token', res.data.access_token)
      if (res.data.refresh_token) {
        uni.setStorageSync('refresh_token', res.data.refresh_token)
      }
      return res.data.access_token
    }
    return null
  } catch (e) {
    console.error('刷新token失败:', e)
    return null
  }
}

// 请求封装（所有 API 模块共用）
const request = (options) => {
  const { url, method = 'GET', data = {}, params = {}, header = {} } = options

  // 网络不可用时直接拒绝，不发起请求
  // 动态导入 useNetwork 避免循环依赖
  try {
    const { isOffline } = require('@/composables/useNetwork.js')
    if (isOffline && isOffline.value) {
      return Promise.reject({ errMsg: 'network offline', code: 'OFFLINE' })
    }
  } catch (_) { /* 如果模块未加载，忽略 */ }

  // 添加 token 到 Authorization 请求头
  const token = uni.getStorageSync('token')
  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  // 构建URL，添加查询参数（token 不再通过 params 传递）
  let fullUrl = `${BASE_URL}${url}`
  if (params && Object.keys(params).length > 0) {
    const queryString = Object.keys(params)
      .filter(key => key !== 'token')  // 过滤掉旧代码中可能残留的 token 参数
      .map(key => `${key}=${encodeURIComponent(params[key])}`)
      .join('&')
    if (queryString) {
      fullUrl = `${fullUrl}?${queryString}`
    }
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        ...header
      },
      success: async (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // Token 过期，尝试刷新
          if (!isRefreshing) {
            isRefreshing = true
            const newToken = await refreshAccessToken()
            isRefreshing = false

            if (newToken) {
              // 刷新成功，重试原请求
              onRefreshed(newToken)
              header['Authorization'] = `Bearer ${newToken}`
              uni.request({
                url: fullUrl,
                method,
                data,
                header: {
                  'Content-Type': 'application/json',
                  ...header
                },
                success: (retryRes) => {
                  if (retryRes.statusCode === 200) resolve(retryRes.data)
                  else reject(retryRes)
                },
                fail: reject
              })
              return
            }
          } else {
            // 已有刷新进行中，等待刷新完成后重试
            addRefreshSubscriber((newToken) => {
              header['Authorization'] = `Bearer ${newToken}`
              uni.request({
                url: fullUrl,
                method,
                data,
                header: {
                  'Content-Type': 'application/json',
                  ...header
                },
                success: (retryRes) => {
                  if (retryRes.statusCode === 200) resolve(retryRes.data)
                  else reject(retryRes)
                },
                fail: reject
              })
            })
            return
          }

          // 刷新失败，清除登录状态
          console.error('Token过期，请重新登录')
          uni.removeStorageSync('token')
          uni.removeStorageSync('refresh_token')
          uni.showToast({
            title: '登录已过期，请重新登录',
            icon: 'none',
            duration: 2000
          })
          setTimeout(() => {
            uni.reLaunch({ url: '/pages/login/index' })
          }, 2000)
          reject(res)
        } else {
          reject(res)
        }
      },
      fail: (err) => {
        // 检测是否为网络错误 → 标记离线
        const errMsg = (err && err.errMsg) || ''
        if (
          errMsg.includes('fail') ||
          errMsg.includes('timeout') ||
          errMsg.includes('network')
        ) {
          try {
            const { isOffline: netOffline } = require('@/composables/useNetwork.js')
            if (netOffline) netOffline.value = true
          } catch (_) {}
        }
        reject(err)
      }
    })
  })
}

export default request
// 导出所有API模块
export * from './auth'
export * from './family'
export * from './device'
export * from './scene'
export * from './gateway'
export * from './agent'
