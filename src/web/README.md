# SmartHome — 前端

基于 **Vue 3 + uni-app + Vite + Pinia** 的智能家居前端，支持移动端（H5 / 小程序）和桌面端自适应。

---

## 页面结构

```
src/pages/
├── index/              # 首页 — 环境监测仪表盘（温湿度/光照/人体红外）
├── devices/            # 灯光 — 灯光远程开关 + 状态
├── scenes/             # 电机 — 电风扇/蜂鸣器控制
├── profile/            # 设备 — 设备列表管理
├── data-analysis/      # 分析 — 数据分析看板
├── data-alert/         # 预警 — AI 夜间异常预警
├── login/              # 登录
├── family/             # 家庭管理
├── dashboard/          # [旧] 待迁移
```

## 底部导航（5 Tab）

| Tab | 路径 | 说明 |
|---|---|---|
| 首页 | `/pages/index/index` | 环境监测 |
| 灯光 | `/pages/devices/index` | 设备控制 |
| 电机 | `/pages/scenes/index` | 场景控制 |
| 设备 | `/pages/profile/index` | 设备管理 |
| 分析 | `/pages/data-analysis/index` | 数据分析 |

分析页内可跳转"预警"页，预警页可返回。

## 自适应布局

| 设备 | 宽度 | Tab 位置 |
|---|---|---|
| 移动端 | < 768px | 底部固定 |
| 桌面端 | >= 768px | 左侧侧边栏（默认收起 56px，悬停展开 220px） |
| 大屏 | >= 1200px | 左侧侧边栏（默认收起 56px，悬停展开 240px） |

侧边栏底部有 `◀/▶` 按钮可手动锁定展开/收起状态。

## 技术栈

- Vue 3 (Composition API + `<script setup>`)
- uni-app 3 + Vite 5
- Pinia 状态管理
- SCSS + 响应式断点

## 目录结构

```
web/
├── src/
│   ├── api/                 # API 调用封装
│   │   ├── index.js         # 基础请求（token 刷新/拦截）
│   │   ├── auth.js          # 认证
│   │   ├── device.js        # 设备
│   │   ├── scene.js         # 场景
│   │   ├── family.js        # 家庭
│   │   ├── gateway.js       # 网关
│   │   └── agent.js         # AI 智能体
│   ├── components/
│   │   ├── CustomTabBar.vue # 底部导航/侧边栏
│   │   ├── NetworkGuard.vue # 网络状态守卫
│   │   ├── SceneCard.vue    # 场景卡片
│   │   └── AiAssistant.vue  # AI 助手
│   ├── composables/         # 逻辑复用
│   │   ├── useBreakpoint.js   # 响应式断点检测
│   │   ├── useNetwork.js      # 网络状态
│   │   ├── useSensorData.js   # 传感器数据轮询
│   │   └── useDeviceConnection.js  # 设备连接状态
│   ├── store/               # Pinia
│   │   ├── user.js          # 用户登录态
│   │   └── theme.js         # 主题
│   ├── styles/
│   │   ├── responsive.scss  # 响应式断点 + 混入
│   │   ├── theme.scss       # 主题变量
│   │   └── variables.scss   # 设计变量
│   ├── data/
│   │   └── alertData.ts     # 预警数据类型定义
│   ├── utils/
│   │   ├── websocket.js     # WebSocket 连接管理
│   │   └── format.js        # 格式化工具
│   ├── App.vue              # 根组件（初始化断点检测）
│   ├── main.js              # 入口
│   ├── pages.json           # 页面路由 + Tab 配置
│   └── manifest.json        # uni-app 配置
├── public/data/             # 静态数据（分析页兜底 CSV）
├── vite.config.ts           # 代理配置
├── package.json
└── tsconfig.json
```

## 本地运行

```bash
cd web
npm install
npm run dev:h5          # H5 浏览器开发
npm run build:h5        # H5 构建
npm run dev:mp-weixin   # 微信小程序开发
npm run build:mp-weixin # 微信小程序构建
```

## API 代理

Vite dev server（5177）将 API 请求转发到本地后端微服务：

| 路径前缀 | 转发到 | 服务 |
|---|---|---|
| `/api/v1/auth` | 8011 | 用户认证 |
| `/api/v1/family` | 8011 | 家庭管理 |
| `/api/v1/devices` | 8012 | 设备管理 |
| `/api/v1/control` | 8012 | 设备控制 |
| `/api/v1/data` | 8012 | 数据查询 |
| `/api/v1/analysis` | 8012 | 数据分析 |
| `/api/v1/scenes` | 8014 | 场景 |
| `/api/v1/agent` | 8013 | AI 智能体 |
| `/connections` | 8010 | 网关连接 |
| `/ws` | 8010 | WebSocket |
| `/api/v1/agent/ws` | 8013 | AI WebSocket |

## 桌面端适配逻辑

`App.vue` 启动时通过 `initBreakpoint()` 检测屏幕宽度，设置 `<html>` 的 `data-device` 属性和 `.desktop` / `.mobile` class。各页面通过 `useBreakpoint()` composable 获取 `isDesktop` 响应式值来控制布局。

- 移动端：底部 Tab + 全屏内容
- 桌面端：左侧侧边栏 + 内容区 `margin-left` 避开侧边栏
