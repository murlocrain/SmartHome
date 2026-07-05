# 智能家居IoT平台 - API接口文档

## 目录

1. [概述](#概述)
2. [认证机制](#认证机制)
3. [响应格式](#响应格式)
4. [用户服务](#用户服务)
5. [家庭管理](#家庭管理)
6. [设备管理](#设备管理)
7. [场景服务](#场景服务)
8. [网关服务](#网关服务)

---

## 概述

本文档描述智能家居IoT平台的后端API接口。平台采用微服务架构，各服务独立部署：

| 服务 | 端口 | 描述 |
|------|------|------|
| 用户服务 | 8001 | 用户认证、家庭管理 |
| 设备服务 | 8002 | 设备注册、分组管理 |
| 场景服务 | 8003 | 场景规则、自动化 |
| 网关服务 | 8000 | WebSocket实时通信 |

---

## 认证机制

### 认证方式

- **JWT Token**: 所有API请求需在请求头中携带 `Authorization: Bearer <token>`
- **WebSocket**: 通过URL参数 `token` 传递

### Token 获取

```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
    "username": "string",
    "password": "string"
}
```

---

## 响应格式

所有API响应统一格式：

```json
{
    "code": 200,
    "message": "success",
    "data": {}
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| code | int | 状态码，200表示成功 |
| message | string | 响应消息 |
| data | any | 响应数据 |

---

## 用户服务

**基础路径**: `/api/v1/auth`

### 1. 用户注册

```http
POST /api/v1/auth/register HTTP/1.1
Content-Type: application/json

{
    "username": "string (必填, 3-50字符)",
    "email": "string (可选, 邮箱格式)",
    "phone": "string (可选)",
    "password": "string (必填, 6-128字符)"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "username": "user1",
        "email": "user@example.com",
        "phone": "13800138000",
        "is_active": true,
        "created_at": "2024-01-01T12:00:00"
    }
}
```

### 2. 用户登录

```http
POST /api/v1/auth/login HTTP/1.1
Content-Type: application/json

{
    "username": "string (必填)",
    "password": "string (必填)"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
    }
}
```

### 3. 获取当前用户

```http
GET /api/v1/auth/me HTTP/1.1
Authorization: Bearer <token>
```

### 4. 更新用户信息

```http
PUT /api/v1/auth/me HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
    "email": "string (可选)",
    "phone": "string (可选)",
    "is_active": "bool (可选)"
}
```

### 5. 修改密码

```http
POST /api/v1/auth/change-password HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
    "old_password": "string (必填)",
    "new_password": "string (必填, 6-128字符)"
}
```

### 6. 获取隐私设置

```http
GET /api/v1/auth/privacy HTTP/1.1
Authorization: Bearer <token>
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "personalization": true,
        "data_collection": true
    }
}
```

### 7. 更新隐私设置

```http
PUT /api/v1/auth/privacy HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
    "personalization": "bool (可选)",
    "data_collection": "bool (可选)"
}
```

---

## 家庭管理

**基础路径**: `/api/v1/family`

### 1. 创建家庭

```http
POST /api/v1/family/create HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "string (必填, 1-100字符)"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "name": "我的家",
        "owner_id": 1,
        "created_at": "2024-01-01T12:00:00"
    }
}
```

### 2. 获取用户家庭列表

```http
GET /api/v1/family/list HTTP/1.1
Authorization: Bearer <token>
```

### 3. 获取家庭详情

```http
GET /api/v1/family/{family_id} HTTP/1.1
Authorization: Bearer <token>
```

### 4. 添加家庭成员

```http
POST /api/v1/family/{family_id}/members HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_id": "int (必填, 被添加用户ID)",
    "role": "string (可选, 角色: admin/member, 默认member)"
}
```

### 5. 获取家庭成员

```http
GET /api/v1/family/{family_id}/members HTTP/1.1
Authorization: Bearer <token>
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "family_id": 1,
            "user_id": 1,
            "role": "admin",
            "joined_at": "2024-01-01T12:00:00"
        }
    ]
}
```

### 6. 移除家庭成员

```http
DELETE /api/v1/family/{family_id}/members/{user_id} HTTP/1.1
Authorization: Bearer <token>
```

### 7. 创建房间

```http
POST /api/v1/family/{family_id}/rooms HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "string (必填, 1-100字符)"
}
```

### 8. 获取房间列表

```http
GET /api/v1/family/{family_id}/rooms HTTP/1.1
Authorization: Bearer <token>
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "客厅",
            "family_id": 1,
            "created_at": "2024-01-01T12:00:00"
        }
    ]
}
```

### 9. 删除房间

```http
DELETE /api/v1/family/rooms/{room_id} HTTP/1.1
Authorization: Bearer <token>
```

---

## 设备管理

**基础路径**: `/api/v1/devices`

**认证方式**: URL参数 `token` (Query参数)

### 1. 设备注册

```http
POST /api/v1/devices/register?token=<token> HTTP/1.1
Content-Type: application/json

{
    "device_id": "string (必填, 1-64字符, 设备唯一标识)",
    "device_type": "string (必填, 设备类型)",
    "name": "string (可选, 设备名称)",
    "family_id": "int (必填, 所属家庭)",
    "room_id": "int (可选, 所属房间)",
    "capabilities": "object (可选, 设备能力)",
    "config": "object (可选, 设备配置)"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "device_id": "device001",
        "device_type": "light",
        "name": "客厅灯",
        "family_id": 1,
        "room_id": 1,
        "capabilities": {},
        "is_online": false,
        "last_seen": null,
        "created_at": "2024-01-01T12:00:00"
    }
}
```

### 2. 获取设备列表

```http
GET /api/v1/devices/list?family_id=1&room_id=2&token=<token> HTTP/1.1
```

**参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| family_id | int | 是 | 家庭ID |
| room_id | int | 否 | 房间ID |
| token | string | 是 | 认证令牌 |

### 3. 获取设备详情

```http
GET /api/v1/devices/{device_id}?token=<token> HTTP/1.1
```

### 4. 更新设备信息

```http
PUT /api/v1/devices/{device_id}?token=<token> HTTP/1.1
Content-Type: application/json

{
    "name": "string (可选)",
    "room_id": "int (可选)",
    "config": "object (可选)"
}
```

### 5. 解绑设备

```http
DELETE /api/v1/devices/{device_id}?token=<token> HTTP/1.1
```

### 6. 创建设备分组

```http
POST /api/v1/devices/groups?token=<token> HTTP/1.1
Content-Type: application/json

{
    "name": "string (必填, 1-100字符)",
    "family_id": "int (必填, 所属家庭)"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "name": "客厅设备组",
        "family_id": 1,
        "created_at": "2024-01-01T12:00:00"
    }
}
```

### 7. 获取分组列表

```http
GET /api/v1/devices/groups?family_id=1&token=<token> HTTP/1.1
```

### 8. 添加设备到分组

```http
POST /api/v1/devices/groups/{group_id}/devices/{device_db_id}?token=<token> HTTP/1.1
```

**注意**: `device_db_id` 是设备的数据库ID，非device_id。

### 9. 从分组移除设备

```http
DELETE /api/v1/devices/groups/{group_id}/devices/{device_db_id}?token=<token> HTTP/1.1
```

### 10. 获取分组设备列表

```http
GET /api/v1/devices/groups/{group_id}/devices?token=<token> HTTP/1.1
```

### 11. 删除分组

```http
DELETE /api/v1/devices/groups/{group_id}?token=<token> HTTP/1.1
```

---

## 场景服务

**基础路径**: `/api/v1/scenes`

### 1. 创建场景规则

```http
POST /api/v1/scenes/rules HTTP/1.1
Content-Type: application/json

{
    "family_id": "int (必填)",
    "name": "string (必填, 规则名称)",
    "scene_id": "string (必填, 场景唯一标识)",
    "conditions": "object (必填, 触发条件)",
    "actions": "array (必填, 执行动作)"
}
```

**conditions 格式示例**:
```json
{
    "temperature": { "operator": ">", "value": 28 },
    "humidity": { "operator": "<", "value": 30 },
    "has_person": true
}
```

**actions 格式示例**:
```json
[
    {
        "device_id": "device001",
        "command": "on",
        "params": {}
    }
]
```

**响应**:
```json
{
    "id": 1,
    "name": "温度过高自动开空调",
    "scene_id": "auto_ac_on"
}
```

### 2. 获取家庭场景规则

```http
GET /api/v1/scenes/rules/{family_id} HTTP/1.1
```

**响应**:
```json
[
    {
        "id": 1,
        "name": "温度过高自动开空调",
        "scene_id": "auto_ac_on"
    }
]
```

### 3. 更新场景规则

```http
PUT /api/v1/scenes/rules/{rule_id} HTTP/1.1
Content-Type: application/json

{
    "name": "string (可选)",
    "conditions": "object (可选)",
    "actions": "array (可选)"
}
```

**响应**:
```json
{
    "success": true
}
```

### 4. 删除场景规则

```http
DELETE /api/v1/scenes/rules/{rule_id} HTTP/1.1
```

**响应**:
```json
{
    "success": true
}
```

### 5. 手动触发场景评估

```http
POST /api/v1/scenes/trigger/{family_id} HTTP/1.1
Content-Type: application/json

{
    "temperature": 28.5,
    "humidity": 45.0,
    "has_person": true
}
```

**响应**:
```json
{
    "message": "Scene evaluation triggered"
}
```

### 6. 获取房间状态

```http
GET /api/v1/scenes/state/{family_id} HTTP/1.1
```

**响应**:
```json
{
    "family_id": 1,
    "temperature": 25.5,
    "humidity": 45.0,
    "illumination": 300.0,
    "has_person": true,
    "smoke_detected": false,
    "wifi_connected": true,
    "last_update": "2024-01-01T12:00:00"
}
```

### 7. 获取历史数据

```http
GET /api/v1/scenes/history/{family_id}?hours=24 HTTP/1.1
```

**参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| hours | int | 否 | 查询小时数，默认24 |

### 8. 获取场景事件日志

```http
GET /api/v1/scenes/events/{family_id}?hours=24 HTTP/1.1
```

**响应**:
```json
[
    {
        "id": 1,
        "scene_id": "auto_ac_on",
        "scene_name": "温度过高自动开空调",
        "description": "温度超过28度，自动开启空调",
        "suggestion": "建议设置温度为26度",
        "priority": "info",
        "created_at": "2024-01-01T12:00:00"
    }
]
```

### 9. WebSocket连接

```
ws://localhost:8003/api/v1/scenes/ws/{family_id}
```

用于接收实时场景事件推送。

---

## 网关服务

**基础路径**: `/`

**端口**: 8000

### 1. WebSocket连接

```
ws://localhost:8000/ws/{family_id}?token={access_token}
```

**连接示例**:
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${familyId}?token=${accessToken}`);

ws.onopen = () => {
    console.log('WebSocket connected');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    switch (message.type) {
        case 'device_update':
            console.log('设备更新:', message.data);
            break;
        case 'command_sent':
            console.log('命令已发送:', message.device_id);
            break;
        case 'pong':
            console.log('心跳响应');
            break;
    }
};

ws.onclose = () => {
    console.log('WebSocket disconnected');
};
```

### 2. 发送设备控制命令

```javascript
ws.send(JSON.stringify({
    "device_id": "device001",
    "command": { "action": "on" }
}));
```

### 3. 心跳检测

发送:
```json
{
    "type": "ping"
}
```

响应:
```json
{
    "type": "pong",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### 4. 获取连接状态

```http
GET /connections HTTP/1.1
```

**响应**:
```json
{
    "active_families": 5,
    "total_connections": 12
}
```

### 5. 健康检查

```http
GET /health HTTP/1.1
```

**响应**:
```json
{
    "status": "healthy",
    "service": "gateway-service"
}
```

### 6. 就绪检查

```http
GET /ready HTTP/1.1
```

**响应**:
```json
{
    "status": "ready"
}
```

---

## WebSocket 消息类型

| 类型 | 方向 | 描述 |
|------|------|------|
| ping | 客户端→服务端 | 心跳请求 |
| pong | 服务端→客户端 | 心跳响应 |
| device_update | 服务端→客户端 | 设备状态更新 |
| command_sent | 服务端→客户端 | 命令发送确认 |

---

## 错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权/令牌无效 |
| 403 | 访问被拒绝 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## MQTT 协议

华为云IoTDA MQTT Topic格式：

### 订阅主题

| 主题 | 描述 |
|------|------|
| `$oc/devices/{device_id}/sys/data/up` | 设备数据上报 |

### 发布主题

| 主题 | 描述 |
|------|------|
| `$oc/devices/{device_id}/sys/commands/request_id={request_id}` | 设备命令下发 |

---

## 设备类型

| device_type | 描述 |
|-------------|------|
| light | 灯光 |
| switch | 开关 |
| air_conditioner | 空调 |
| heater | 加热器 |
| fan | 风扇 |
| curtain | 窗帘 |
| door_lock | 门锁 |
| sensor | 传感器 |

---

## 更新日志

### v1.0.0 (当前版本)
- 用户认证：注册、登录、用户信息管理、隐私设置
- 家庭管理：家庭创建、成员管理、房间管理
- 设备管理：设备注册、分组管理
- 场景服务：场景规则、WebSocket实时推送
- 网关服务：WebSocket实时通信、华为云IoTDA集成