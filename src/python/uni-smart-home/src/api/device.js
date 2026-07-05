// 设备管理相关API
// 使用vite代理，代理配置在vite.config.ts中
const DEVICE_BASE_URL = '/api/v1'

const deviceRequest = (options) => {
  const { url, method = 'GET', data = {}, header = {} } = options
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${DEVICE_BASE_URL}${url}`,
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

// 注册设备
export const registerDevice = (data) => {
  return deviceRequest({
    url: '/devices/register',
    method: 'POST',
    data
  })
}

// 获取设备列表
export const getDeviceList = (familyId, roomId = null) => {
  let url = `/devices/list?family_id=${familyId}`
  if (roomId) {
    url += `&room_id=${roomId}`
  }
  return deviceRequest({
    url,
    method: 'GET'
  })
}

// 获取设备详情
export const getDeviceDetail = (deviceId) => {
  return deviceRequest({
    url: `/devices/${deviceId}`,
    method: 'GET'
  })
}

// 更新设备信息
export const updateDevice = (deviceId, data) => {
  return deviceRequest({
    url: `/devices/${deviceId}`,
    method: 'PUT',
    data
  })
}

// 解绑设备
export const unbindDevice = (deviceId) => {
  return deviceRequest({
    url: `/devices/${deviceId}`,
    method: 'DELETE'
  })
}

// 创建设备分组
export const createDeviceGroup = (data) => {
  return deviceRequest({
    url: '/devices/groups',
    method: 'POST',
    data
  })
}

// 获取分组列表
export const getGroupList = (familyId) => {
  return deviceRequest({
    url: `/devices/groups?family_id=${familyId}`,
    method: 'GET'
  })
}

// 添加设备到分组
export const addDeviceToGroup = (groupId, deviceDbId) => {
  return deviceRequest({
    url: `/devices/groups/${groupId}/devices/${deviceDbId}`,
    method: 'POST'
  })
}

// 从分组移除设备
export const removeDeviceFromGroup = (groupId, deviceDbId) => {
  return deviceRequest({
    url: `/devices/groups/${groupId}/devices/${deviceDbId}`,
    method: 'DELETE'
  })
}

// 获取分组设备列表
export const getGroupDevices = (groupId) => {
  return deviceRequest({
    url: `/devices/groups/${groupId}/devices`,
    method: 'GET'
  })
}

// 删除分组
export const deleteGroup = (groupId) => {
  return deviceRequest({
    url: `/devices/groups/${groupId}`,
    method: 'DELETE'
  })
}

// 获取最新环境监测数据
export const getLatestEnvData = (familyId, limit = 10) => {
  return deviceRequest({
    url: `/devices/env-data/latest?family_id=${familyId}&limit=${limit}`,
    method: 'GET'
  })
}

// 获取房间当前状态（环境监测数据）
export const getEnvRoomState = (familyId) => {
  return deviceRequest({
    url: `/devices/env-data/room-state?family_id=${familyId}`,
    method: 'GET'
  })
}

// 初始化华为云设备
export const initHuaweiDevice = (familyId) => {
  return deviceRequest({
    url: `/devices/init-huawei-device?family_id=${familyId}`,
    method: 'POST'
  })
}

// 从华为云同步历史数据到本地
export const syncHuaweiData = (familyId, days = 7) => {
  return deviceRequest({
    url: `/devices/sync-huawei-data?family_id=${familyId}&days=${days}`,
    method: 'POST'
  })
}
