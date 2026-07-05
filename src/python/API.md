# 智能家居后端 - API 文档

Base URL: `http://localhost:8000`

> 也可以启动服务后打开 `http://localhost:8000/docs` 查看 Swagger UI，或 `http://localhost:8000/redoc` 查看 ReDoc 风格。

---

## 目录

1. [根路径 & 健康检查](#1-根路径--健康检查)
2. [设备控制](#2-设备控制核心功能)
3. [设备管理](#3-设备管理)
4. [环境数据](#4-环境数据)
5. [AI 智能体](#5-ai-智能体)
6. [华为云回调](#6-华为云回调)

---

## 1. 根路径 & 健康检查

### `GET /`

**说明**：返回服务状态信息。

**响应示例**：

```json
{
    "message": "智能家居后端服务运行中（模块化架构）",
    "database": "mysql",
    "huawei_iot": true,
    "version": "2.0.0"
}
```

---

### `GET /health`

**说明**：健康检查，用于部署时的健康探针。

**响应示例**：

```json
{
    "status": "healthy"
}
```

---

## 2. 设备控制（核心功能）

### `POST /control/light`

**说明**：控制灯光开关。

**请求体**：

```json
{
    "action": "ON"
}
```

| 字段 | 类型 | 可选值 | 必填 |
|------|------|--------|------|
| `action` | string | `ON`, `OFF` | ✅ |

**成功响应**：

```json
{
    "message": "light_control 命令下发成功",
    "status": "success",
    "command_name": "light_control",
    "paras": {
        "onoff": "ON"
    }
}
```

**发往华为云的实际 JSON**：

```json
{
    "service_id": "rk2206远程控制",
    "command_name": "light_control",
    "paras": {
        "onoff": "ON"
    }
}
```

---

### `POST /control/motor`

**说明**：控制电风扇开关。

**请求体**：

```json
{
    "action": "ON"
}
```

| 字段 | 类型 | 可选值 | 必填 |
|------|------|--------|------|
| `action` | string | `ON`, `OFF` | ✅ |

**成功响应**：

```json
{
    "message": "motor_control 命令下发成功",
    "status": "success",
    "command_name": "motor_control",
    "paras": {
        "onoff": "ON"
    }
}
```

**发往华为云的实际 JSON**：

```json
{
    "service_id": "rk2206远程控制",
    "command_name": "motor_control",
    "paras": {
        "onoff": "ON"
    }
}
```

---

### `POST /control/beep`

**说明**：蜂鸣器响一下（无参数）。

**请求体**：空 或 `{}`

**成功响应**：

```json
{
    "message": "beep_play 命令下发成功",
    "status": "success",
    "command_name": "beep_play",
    "paras": {}
}
```

**发往华为云的实际 JSON**：

```json
{
    "service_id": "rk2206远程控制",
    "command_name": "beep_play",
    "paras": {}
}
```

---

## 3. 设备管理

### `POST /devices/register`

**说明**：注册一台新设备到数据库。

**请求体**：

```json
{
    "device_id": "6a2179727f2e6c302f77aaf8_env_monitor_02",
    "device_type": "env_monitor",
    "name": "卧室环境监测",
    "family_id": 1
}
```

**响应示例**：

```json
{
    "message": "设备注册成功",
    "device_id": "6a2179727f2e6c302f77aaf8_env_monitor_02"
}
```

---

### `GET /devices/list`

**说明**：获取数据库中所有设备列表。

**响应示例**：

```json
{
    "message": "设备列表获取成功",
    "count": 1,
    "devices": [
        {
            "id": 1,
            "device_id": "6a2179727f2e6c302f77aaf8_env_monitor_01",
            "device_type": "env_monitor",
            "name": "环境监测设备",
            "is_online": true,
            "last_seen": "2026-06-18T09:04:26",
            "created_at": "2026-06-15T13:21:52"
        }
    ]
}
```

---

### `GET /devices/{device_id}`

**说明**：查询单台设备的详细信息（会先尝试从华为云查询，失败则回退到本地数据库）。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `device_id` | string | 华为云设备 ID，例如 `6a2179727f2e6c302f77aaf8_env_monitor_01` |

---

## 4. 环境数据

### `GET /data/latest/{device_id}`

**说明**：获取指定设备最新一条上报的环境数据。

**响应示例**：

```json
{
    "message": "最新数据查询成功",
    "data": {
        "temperature": "33.92424011230469",
        "humidity": "30.109102249145508",
        "light": 239,
        "body_state": "无人",
        "timestamp": "2026-06-18 09:04:26"
    }
}
```

---

### `GET /data/history/{device_id}`

**说明**：获取指定设备的历史环境数据。

**查询参数**：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | int | 20 | 返回的条数 |

**响应示例**：

```json
{
    "message": "历史数据查询成功",
    "count": 3,
    "data": [
        {
            "temperature": "33.92424011230469",
            "humidity": "30.109102249145508",
            "light": 239,
            "body_state": "无人",
            "timestamp": "2026-06-18 09:04:26"
        }
    ]
}
```

---

### `GET /sync`

**说明**：主动从华为云同步一次最新数据。默认使用数据回调机制即可，这个接口用于手动触发。

---

## 5. AI 智能体

### `POST /ai/chat`

**说明**：单纯和 AI 聊天，不控制任何设备。

**请求体**：

```json
{
    "message": "你好，你能做什么？"
}
```

**响应示例**：

```json
{
    "message": "你好，你能做什么？",
    "reply": "你好呀！我可以帮你控制家里的灯光、电风扇和蜂鸣器。试试跟我说'帮我把灯打开'吧。",
    "model": "deepseek-chat"
}
```

---

### `POST /ai/agent` ⭐ 推荐接口

**说明**：**智能体核心接口** — 用户说一句话，AI 自动解析意图并下发设备命令，同时结合环境数据给出建议。

**请求体**：

```json
{
    "message": "帮我把灯打开"
}
```

**更多示例请求**：

| message | 效果 |
|---------|------|
| `"天气太热了，开下风扇"` | 下发 `motor_control ON` |
| `"响一下蜂鸣器"` | 下发 `beep_play` |
| `"关灯"` | 下发 `light_control OFF` |
| `"现在家里什么情况？"` | 返回环境数据 + AI 分析建议 |

**响应示例**：

```json
{
    "message": "帮我把灯打开",
    "reply": "好的，已经为你打开灯光。",
    "parsed": {
        "intent": "control",
        "target": "light",
        "action": "ON"
    },
    "device_result": {
        "success": true,
        "delivered": true,
        "device_timeout": true,
        "status_code": 200
    },
    "current_env": {
        "temperature": "33.92424011230469",
        "humidity": "30.109102249145508",
        "light": 239,
        "body_state": "无人",
        "timestamp": "2026-06-18 09:04:26"
    },
    "env_suggestion": "温度偏高且湿度较低，建议开启空调并适当使用加湿器。"
}
```

| 字段 | 说明 |
|------|------|
| `parsed.intent` | AI 识别的意图：`control` / `question` / `chat` |
| `parsed.target` | 目标设备：`light` / `motor` / `beep` |
| `parsed.action` | 动作：`ON` / `OFF` / `null` |
| `device_result` | 华为云命令下发结果（成功时含 `success: true`） |
| `current_env` | 最新的环境传感器数据 |
| `env_suggestion` | AI 基于环境数据给出的中文建议 |

---

### `POST /ai/analyze-env`

**说明**：让 AI 分析当前环境数据并给出人性化建议。不需要传参数。

**响应示例**：

```json
{
    "current_env": {
        "temperature": "33.92424011230469",
        "humidity": "30.109102249145508",
        "light": 239,
        "body_state": "无人",
        "timestamp": "2026-06-18 09:04:26"
    },
    "suggestion": "温度偏高且湿度较低，建议开启空调并适当使用加湿器。"
}
```

---

## 6. 华为云回调

### `POST /api/v1/devices/huawei-callback`

**说明**：华为云 IoTDA 数据转发回调接口。当设备上报温湿度/光照/人体红外等数据时，华为云会 POST 到这里，后端自动解析并写入 MySQL。

**典型的华为云回调 JSON（节选）**：

```json
{
    "notify_data": {
        "header": {
            "device_id": "6a2179727f2e6c302f77aaf8_env_monitor_01"
        },
        "body": {
            "services": [
                {
                    "service_id": "rk2206远程控制",
                    "properties": {
                        "sht30_temperature": 31.32,
                        "sht30_humidity": 37.73,
                        "bh1750": 247,
                        "body_infrared": "有人",
                        "pir": {
                            "state": "有人"
                        }
                    }
                }
            ]
        }
    }
}
```

**响应**：HTTP 200，返回 `{"status": "success", "message": "Callback received"}`。

> 💡 这是**后端内部接口**，前端一般不需要调用它。部署到公网时需要把这个 URL 告诉华为云控制台的数据转发规则。

---

## 前端对接快速参考

### 用 fetch 控制灯光

```js
fetch('http://localhost:8000/control/light', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'ON' })
}).then(r => r.json()).then(console.log)
```

### 用 axios + AI 智能体

```js
import axios from 'axios'

const { data } = await axios.post('http://localhost:8000/ai/agent', {
    message: '帮我开下风扇'
})
console.log(data.reply)  // '好的，已经为你打开电风扇。'
```

### 用小程序 wx.request 获取最新环境数据

```js
wx.request({
    url: 'http://localhost:8000/data/latest/6a2179727f2e6c302f77aaf8_env_monitor_01',
    success: (res) => {
        console.log('温度：', res.data.data.temperature)
    }
})
```

---

## 完整接口一览

| # | Method | Path | 用途 |
|---|--------|------|------|
| 1 | GET | `/` | 根路径 |
| 2 | GET | `/health` | 健康检查 |
| 3 | POST | `/control/light` | 控制灯光 |
| 4 | POST | `/control/motor` | 控制电风扇 |
| 5 | POST | `/control/beep` | 蜂鸣器响一下 |
| 6 | POST | `/devices/register` | 注册新设备 |
| 7 | GET | `/devices/list` | 设备列表 |
| 8 | GET | `/devices/{device_id}` | 查询单设备 |
| 9 | GET | `/data/latest/{device_id}` | 最新环境数据 |
| 10 | GET | `/data/history/{device_id}` | 历史环境数据 |
| 11 | GET | `/sync` | 手动同步华为云数据 |
| 12 | POST | `/ai/chat` | AI 对话 |
| 13 | POST | `/ai/agent` | **AI 智能体（自然语言控制）** |
| 14 | POST | `/ai/analyze-env` | AI 环境分析 |
| 15 | POST | `/api/v1/devices/huawei-callback` | 华为云数据回调 |

