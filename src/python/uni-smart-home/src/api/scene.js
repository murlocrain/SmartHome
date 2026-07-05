// 场景服务相关API
// 使用vite代理，代理配置在vite.config.ts中
const SCENE_BASE_URL = '/api/v1'

const sceneRequest = (options) => {
  const { url, method = 'GET', data = {}, params = {}, header = {} } = options
  return new Promise((resolve, reject) => {
    // 构建URL，添加查询参数
    let fullUrl = `${SCENE_BASE_URL}${url}`
    if (params && Object.keys(params).length > 0) {
      const queryString = Object.keys(params)
        .map(key => `${key}=${encodeURIComponent(params[key])}`)
        .join('&')
      fullUrl = `${fullUrl}?${queryString}`
    }

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

// 创建场景规则
export const createSceneRule = (data) => {
  return sceneRequest({
    url: '/scenes/rules',
    method: 'POST',
    data
  })
}

// 获取家庭场景规则
export const getFamilySceneRules = (familyId) => {
  return sceneRequest({
    url: `/scenes/rules/${familyId}`,
    method: 'GET'
  })
}

// 更新场景规则
export const updateSceneRule = (ruleId, data) => {
  return sceneRequest({
    url: `/scenes/rules/${ruleId}`,
    method: 'PUT',
    data
  })
}

// 删除场景规则
export const deleteSceneRule = (ruleId) => {
  return sceneRequest({
    url: `/scenes/rules/${ruleId}`,
    method: 'DELETE'
  })
}

// 手动触发场景评估
export const triggerSceneEvaluation = (familyId, data) => {
  return sceneRequest({
    url: `/scenes/trigger/${familyId}`,
    method: 'POST',
    data
  })
}

// 获取房间状态
export const getRoomState = (familyId) => {
  return sceneRequest({
    url: `/scenes/state/${familyId}`,
    method: 'GET'
  })
}

// 获取历史数据
export const getSceneHistory = (familyId, hours = 24) => {
  return sceneRequest({
    url: `/scenes/history/${familyId}`,
    method: 'GET',
    params: { hours }
  })
}

// 获取场景事件日志
export const getSceneEvents = (familyId, hours = 24) => {
  return sceneRequest({
    url: `/scenes/events/${familyId}`,
    method: 'GET',
    params: { hours }
  })
}
