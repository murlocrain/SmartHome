// 场景服务相关API
import request from './index'

// 创建场景规则
export const createSceneRule = (data) => {
  return request({
    url: '/scenes/rules',
    method: 'POST',
    data
  })
}

// 获取家庭场景规则
export const getFamilySceneRules = (familyId) => {
  return request({
    url: `/scenes/rules/${familyId}`,
    method: 'GET'
  })
}

// 更新场景规则
export const updateSceneRule = (ruleId, data) => {
  return request({
    url: `/scenes/rules/${ruleId}`,
    method: 'PUT',
    data
  })
}

// 删除场景规则
export const deleteSceneRule = (ruleId) => {
  return request({
    url: `/scenes/rules/${ruleId}`,
    method: 'DELETE'
  })
}

// 手动触发场景评估
export const triggerSceneEvaluation = (familyId, data) => {
  return request({
    url: `/scenes/trigger/${familyId}`,
    method: 'POST',
    data
  })
}

// 获取房间状态
export const getRoomState = (familyId) => {
  return request({
    url: `/scenes/state/${familyId}`,
    method: 'GET'
  })
}

// 获取历史数据
export const getSceneHistory = (familyId, hours = 24) => {
  return request({
    url: `/scenes/history/${familyId}`,
    method: 'GET',
    params: { hours }
  })
}

// 获取场景事件日志
export const getSceneEvents = (familyId, hours = 24) => {
  return request({
    url: `/scenes/events/${familyId}`,
    method: 'GET',
    params: { hours }
  })
}
