// API基础配置 - 使用vite代理
// 代理配置在vite.config.ts中，转发到各后端服务
const BASE_URL = '/api/v1'

// 请求封装
const request = (options) => {
  const { url, method = 'GET', data = {}, params = {}, header = {} } = options

  // 添加token到请求头（用于某些API）
  const token = uni.getStorageSync('token')
  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  // 构建URL，添加查询参数
  let fullUrl = `${BASE_URL}${url}`
  if (params && Object.keys(params).length > 0) {
    const queryString = Object.keys(params)
      .map(key => `${key}=${encodeURIComponent(params[key])}`)
      .join('&')
    fullUrl = `${fullUrl}?${queryString}`
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
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // Token过期或无效，清除登录状态并跳转到登录页
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