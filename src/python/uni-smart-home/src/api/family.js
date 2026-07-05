// 家庭管理相关API
import request from './index'

// 创建家庭
export const createFamily = (data) => {
  return request({
    url: '/family/create',
    method: 'POST',
    data
  })
}

// 获取用户家庭列表
export const getFamilyList = () => {
  return request({
    url: '/family/list',
    method: 'GET'
  })
}

// 获取家庭详情
export const getFamilyDetail = (familyId) => {
  return request({
    url: `/family/${familyId}`,
    method: 'GET'
  })
}

// 添加家庭成员
export const addFamilyMember = (familyId, data) => {
  return request({
    url: `/family/${familyId}/members`,
    method: 'POST',
    data
  })
}

// 获取家庭成员
export const getFamilyMembers = (familyId) => {
  return request({
    url: `/family/${familyId}/members`,
    method: 'GET'
  })
}

// 移除家庭成员
export const removeFamilyMember = (familyId, userId) => {
  return request({
    url: `/family/${familyId}/members/${userId}`,
    method: 'DELETE'
  })
}

// 创建房间
export const createRoom = (familyId, data) => {
  return request({
    url: `/family/${familyId}/rooms`,
    method: 'POST',
    data
  })
}

// 获取房间列表
export const getRoomList = (familyId) => {
  return request({
    url: `/family/${familyId}/rooms`,
    method: 'GET'
  })
}

// 删除房间
export const deleteRoom = (roomId) => {
  return request({
    url: `/family/rooms/${roomId}`,
    method: 'DELETE'
  })
}
