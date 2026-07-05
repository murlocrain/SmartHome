// 用户认证相关API
import request from './index'

// 用户注册
export const register = (data) => {
  return request({
    url: '/auth/register',
    method: 'POST',
    data
  })
}

// 用户登录
export const login = (data) => {
  return request({
    url: '/auth/login',
    method: 'POST',
    data
  })
}

// 获取当前用户
export const getCurrentUser = () => {
  return request({
    url: '/auth/me',
    method: 'GET'
  })
}

// 更新用户信息
export const updateUser = (data) => {
  return request({
    url: '/auth/me',
    method: 'PUT',
    data
  })
}

// 修改密码
export const changePassword = (data) => {
  return request({
    url: '/auth/change-password',
    method: 'POST',
    data
  })
}

// 获取隐私设置
export const getPrivacySettings = () => {
  return request({
    url: '/auth/privacy',
    method: 'GET'
  })
}

// 更新隐私设置
export const updatePrivacySettings = (data) => {
  return request({
    url: '/auth/privacy',
    method: 'PUT',
    data
  })
}
