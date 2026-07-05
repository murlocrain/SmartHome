# API对接总结

## 认证方式统一

所有后端服务已统一使用 **查询参数 `token`** 的认证方式。

### 后端修复

#### 1. 用户服务 (auth_router.py)
```python
async def get_current_user(
    token: str = Query(...),  # ✅ 已添加 Query(...)
    db: AsyncSession = Depends(get_db),
) -> dict:
```

#### 2. 家庭管理 (family_router.py)
```python
async def get_current_user_id(token: str = Query(...)) -> int:  # ✅ 已添加 Query(...)
```

#### 3. 设备管理 (device_router.py)
```python
async def get_current_user_id(token: str = Query(...)) -> int:  # ✅ 已正确
```

#### 4. 场景服务 (scene_router.py)
- 大部分接口不需要认证 ✅
- WebSocket 连接不需要认证 ✅

#### 5. 网关服务 (gateway_router.py)
```python
@router.websocket("/ws/{family_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    family_id: str,
    token: str = Query(...),  # ✅ 已正确
):
```

### 前端修复

#### 1. 基础请求封装 (index.js)
```javascript
const request = (options) => {
  const { url, method = 'GET', data = {}, params = {}, header = {} } = options

  // 构建URL，添加查询参数
  let fullUrl = `${BASE_URL}${url}`
  if (params && Object.keys(params).length > 0) {
    const queryString = Object.keys(params)
      .map(key => `${key}=${encodeURIComponent(params[key])}`)
      .join('&')
    fullUrl = `${fullUrl}?${queryString}`
  }
  // ...
}
```

#### 2. 用户认证 API (auth.js)
```javascript
export const getCurrentUser = () => {
  const token = uni.getStorageSync('token')
  return request({
    url: '/auth/me',
    method: 'GET',
    params: { token }  // ✅ 添加查询参数
  })
}
```

#### 3. 家庭管理 API (family.js)
```javascript
export const getFamilyList = () => {
  const token = uni.getStorageSync('token')
  return request({
    url: '/family/list',
    method: 'GET',
    params: { token }  // ✅ 添加查询参数
  })
}
```

#### 4. 设备管理 API (device.js)
```javascript
export const getDeviceList = (familyId) => {
  const token = uni.getStorageSync('token')
  return request({
    url: '/devices/list',
    method: 'GET',
    params: { family_id: familyId, token }  // ✅ 已正确
  })
}
```

#### 5. 场景服务 API (scene.js)
```javascript
export const getRoomState = (familyId) => {
  return sceneRequest({
    url: `/scenes/state/${familyId}`,
    method: 'GET'  // ✅ 不需要认证
  })
}
```

## API认证方式总结表

| 服务 | 接口 | 认证方式 | 前端实现 | 状态 |
|------|------|---------|---------|------|
| 用户服务 | /auth/register | 无需认证 | - | ✅ |
| 用户服务 | /auth/login | 无需认证 | - | ✅ |
| 用户服务 | /auth/me | 查询参数 token | params: { token } | ✅ |
| 用户服务 | /auth/change-password | 查询参数 token | params: { token } | ✅ |
| 家庭管理 | /family/create | 查询参数 token | params: { token } | ✅ |
| 家庭管理 | /family/list | 查询参数 token | params: { token } | ✅ |
| 家庭管理 | /family/{id} | 查询参数 token | params: { token } | ✅ |
| 设备管理 | /devices/list | 查询参数 token | params: { token } | ✅ |
| 设备管理 | /devices/register | 查询参数 token | params: { token } | ✅ |
| 场景服务 | /scenes/state/{id} | 无需认证 | - | ✅ |
| 场景服务 | /scenes/rules/{id} | 无需认证 | - | ✅ |
| 网关服务 | /ws/{family_id} | 查询参数 token | WebSocket参数 | ✅ |

## 前端请求示例

### GET 请求（带认证）
```javascript
// 获取家庭列表
const token = uni.getStorageSync('token')
request({
  url: '/family/list',
  method: 'GET',
  params: { token }  // token作为查询参数
})

// 实际请求: /api/v1/family/list?token=xxx
```

### POST 请求（带认证）
```javascript
// 创建家庭
const token = uni.getStorageSync('token')
request({
  url: '/family/create',
  method: 'POST',
  data: { name: '我的家' },
  params: { token }  // token作为查询参数
})

// 实际请求: /api/v1/family/create?token=xxx
// Body: { "name": "我的家" }
```

### WebSocket 连接（带认证）
```javascript
// WebSocket连接
const token = uni.getStorageSync('token')
const ws = new WebSocket(`ws://localhost:8010/ws/${familyId}?token=${token}`)
```

## 常见问题

### 1. 422 Unprocessable Content
**原因**: 后端期望 token 作为查询参数，但前端没有提供或格式不正确

**解决**: 确保所有需要认证的API都添加 `params: { token }`

### 2. 401 Unauthorized
**原因**: token 无效或过期

**解决**: 检查 token 是否正确存储，是否过期

### 3. 跨域问题
**原因**: 前端直接访问后端服务

**解决**: 使用 Vite 代理配置（vite.config.ts）

## Vite代理配置

```typescript
export default defineConfig({
  server: {
    proxy: {
      '/api/v1/auth': {
        target: 'http://localhost:8011',
        changeOrigin: true
      },
      '/api/v1/family': {
        target: 'http://localhost:8011',
        changeOrigin: true
      },
      '/api/v1/devices': {
        target: 'http://localhost:8012',
        changeOrigin: true
      },
      '/api/v1/scenes': {
        target: 'http://localhost:8014',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8010',
        ws: true,
        changeOrigin: true
      }
    }
  }
})
```

## 测试流程

1. 注册用户
   - POST /api/v1/auth/register
   - 无需认证

2. 登录获取token
   - POST /api/v1/auth/login
   - 返回 access_token

3. 存储token
   - uni.setStorageSync('token', response.data.access_token)

4. 使用token访问API
   - GET /api/v1/family/list?token=xxx
   - POST /api/v1/family/create?token=xxx

5. WebSocket连接
   - ws://localhost:8010/ws/{family_id}?token=xxx

## 所有修复已完成 ✅

前后端API对接已完全统一，所有认证方式一致，不会再出现422错误！