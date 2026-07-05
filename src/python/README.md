# SmartHome — 智能家居 IoT 平台

基于 **FastAPI（多微服务） + Vue 3（uni-app） + MySQL + 华为云 IoTDA + AI** 的智能家居系统。

---

## 功能特性

- **设备远程控制**：灯光、电风扇、蜂鸣器
- **实时环境监测**：温湿度、光照、人体红外、可燃气体
- **华为云 IoTDA 对接**：设备数据回调入库 + 远程下发命令
- **AI 场景识别**：基于 sklearn 模型自动判别家庭场景（离家/居家/睡眠/活动）
- **数据分析看板**：环境时序图、活动热力图、每日作息时间线、场景分布饼图
- **夜间异常预警**：基于动态基线的 z-score 异常检测
- **AI 智能体**：自然语言一句话控制设备（对接 DeepSeek）

---

## 目录结构

```
smarthome/
├── docker-compose.yml          # Docker 一键部署
├── SETUP.md                    # 部署指南
├── start-all.ps1               # Windows 启动脚本
├── start-all.sh                # Mac/Linux 启动脚本
├── python/                     # 后端
│   ├── start_services.py       # 一键启动所有微服务
│   ├── init_mysql.sql          # MySQL 建表脚本
│   ├── .env.example            # 环境变量模板
│   ├── common/                 # 公共模块
│   │   ├── config.py           # 配置读取
│   │   ├── database.py         # 数据库连接 + ORM 自动建表
│   │   ├── models.py           # SQLAlchemy ORM 模型
│   │   ├── iot_client.py       # 华为云 IoTDA 客户端
│   │   └── ml_models/          # sklearn 模型文件
│   ├── services/
│   │   ├── gateway_service/    # API 网关（8010）
│   │   ├── user_service/       # 用户认证 + 家庭管理（8011）
│   │   ├── device_service/     # 设备管理 + 数据分析（8012）
│   │   ├── agent_service/      # AI 智能体（8013）
│   │   ├── scene_service/      # 场景服务（8014）
│   │   └── ai_service/         # ML 预测引擎
│   └── APP/                    # [旧] 单进程版本，保留兼容
└── web/                        # 前端
    ├── src/pages/
    │   ├── index/              # 首页 — 环境监测
    │   ├── devices/            # 灯光控制
    │   ├── scenes/             # 电机控制
    │   ├── profile/            # 设备管理
    │   ├── data-analysis/      # 数据分析看板
    │   └── data-alert/         # AI 智能预警
    └── vite.config.ts          # 开发代理配置
```

---

## 快速开始

详细步骤见 [SETUP.md](./SETUP.md)。

Docker 一键启动：

```bash
cp python/.env.example python/.env
docker compose up -d
# 打开 http://localhost:5177
```

本地手动启动：

```bash
# 终端 1 — 后端
cd python
cp .env.example .env
pip install -r requirements.txt
python start_services.py

# 终端 2 — 前端
cd web
npm install
npm run dev:h5
```

---

## API 文档

启动后访问各服务 `/docs`：

- 网关: http://localhost:8010/docs
- 用户: http://localhost:8011/docs
- 设备: http://localhost:8012/docs

详细接口文档见 `python/API.md`。
