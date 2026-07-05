// 用户状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getCurrentUser } from '@/api'

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const userInfo = ref(null)
  const token = ref(uni.getStorageSync('token') || '')
  const refreshToken = ref(uni.getStorageSync('refresh_token') || '')

  // 当前家庭
  const currentFamily = ref(null)
  const familyList = ref([])

  // WebSocket 连接
  const wsConnection = ref(null)
  const sceneWsConnection = ref(null)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')

  // 设置token
  const setToken = (newToken, newRefreshToken) => {
    token.value = newToken
    refreshToken.value = newRefreshToken
    uni.setStorageSync('token', newToken)
    uni.setStorageSync('refresh_token', newRefreshToken)
  }

  // 清除token
  const clearToken = () => {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    currentFamily.value = null
    familyList.value = []
    uni.removeStorageSync('token')
    uni.removeStorageSync('refresh_token')
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const res = await getCurrentUser()
      if (res && res.data) {
        userInfo.value = res.data
        return res.data
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果是401错误，已经在API层处理了跳转，这里不需要再次处理
      if (error.statusCode !== 401) {
        clearToken()
      }
      throw error
    }
  }

  // 设置当前家庭
  const setCurrentFamily = (family) => {
    currentFamily.value = family
    uni.setStorageSync('current_family_id', family.id)
  }

  // 设置家庭列表
  const setFamilyList = (list) => {
    familyList.value = list
    // 如果没有当前家庭，默认选择第一个
    if (!currentFamily.value && list.length > 0) {
      setCurrentFamily(list[0])
    }
  }

  // 设置WebSocket连接
  const setWsConnection = (ws) => {
    wsConnection.value = ws
  }

  // 设置场景WebSocket连接
  const setSceneWsConnection = (ws) => {
    sceneWsConnection.value = ws
  }

  // 清除WebSocket连接
  const clearWsConnections = () => {
    if (wsConnection.value) {
      wsConnection.value.close()
      wsConnection.value = null
    }
    if (sceneWsConnection.value) {
      sceneWsConnection.value.close()
      sceneWsConnection.value = null
    }
  }

  // 登出
  const logout = () => {
    clearWsConnections()
    clearToken()
    uni.reLaunch({ url: '/pages/login/index' })
  }

  return {
    userInfo,
    token,
    refreshToken,
    currentFamily,
    familyList,
    wsConnection,
    sceneWsConnection,
    isLoggedIn,
    username,
    setToken,
    clearToken,
    fetchUserInfo,
    setCurrentFamily,
    setFamilyList,
    setWsConnection,
    setSceneWsConnection,
    clearWsConnections,
    logout
  }
})