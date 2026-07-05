# SmartHome — 一键部署指南

clone 下来直接跑，无需手动安装 MySQL / Python / Node.js。

---

## 方式一：Docker 一键部署（推荐）

```bash
# 0. 确保已安装 Docker Desktop
#    https://www.docker.com/products/docker-desktop/

# 1. 进入项目根目录
cd test/zys-dev/src/smarthome

# 2. 复制环境变量（如无特殊需求，默认值即可运行）
cp python/.env.example python/.env

# 3. 启动所有服务（MySQL + 后端 + 前端）
docker compose up -d

# 4. 等待 30 秒初始化完成，然后访问
#    前端: http://localhost:5177
#    API 文档: http://localhost:8010/docs

# 5. 停止
docker compose down
```

首次启动 `docker compose up` 会自动完成：
- 创建 MySQL 容器 + 执行建表 SQL
- 安装 Python 依赖 + 启动 5 个微服务
- 安装 Node 依赖 + 启动 Vite 前端

---

## 方式二：本地手动启动

如果你的电脑已有 Python 3.10+ / Node.js 20+ / MySQL 8.0+：

### 1. 数据库

```bash
# 确保 MySQL 正在运行，然后导入建表 SQL
mysql -u root -p < python/init_mysql.sql
```

### 2. 后端

```bash
cd python

# 创建 .env
cp .env.example .env

# 编辑 .env 填写你的 MySQL 密码
# MYSQL_PASSWORD=你的密码

# 安装依赖
pip install -r requirements.txt

# 启动所有微服务
python start_services.py
```

### 3. 前端

```bash
cd web

npm install
npm run dev:h5
```

### 4. 访问

| 地址 | 说明 |
|---|---|
| `http://localhost:5177` | 前端页面 |
| `http://localhost:8010/docs` | 网关 API 文档 |
| `http://localhost:8011/docs` | 用户服务 API 文档 |
| `http://localhost:8012/docs` | 设备服务 API 文档 |

---

## 华为云 IoTDA 对接（可选）

如果不需要真实设备数据，跳过此节也可正常运行前端。

编辑 `python/.env` 填入华为云 IoTDA 凭证：

```env
HUAWEI_IOTDA_ENABLED=true
HUAWEI_IOTDA_AK=你的AK
HUAWEI_IOTDA_SK=你的SK
HUAWEI_IOTDA_PROJECT_ID=你的项目ID
HUAWEI_IOTDA_INSTANCE_ID=你的实例ID
```

---

## AI 智能体（可选）

编辑 `python/.env` 启用：

```env
AI_ENABLED=true
AI_API_KEY=你的 DeepSeek/OpenAI API Key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
```

---

## 服务端口一览

| 服务 | 端口 |
|---|---|
| MySQL | 3306 |
| 前端 Vite | 5177 |
| 网管服务 Gateway | 8010 |
| 用户服务 User | 8011 |
| 设备服务 Device | 8012 |
| AI 智能体 Agent | 8013 |
| 场景服务 Scene | 8014 |

---

## 常见问题

**Q: Docker 启动后前端白屏？**

等待 MySQL `healthcheck` 通过后后端才启动，首次约需 30-60 秒。查看日志：

```bash
docker compose logs -f backend
```

**Q: 端口被占用？**

修改 `docker-compose.yml` 中的 ports 映射（冒号左边改为你想要的端口号）。

**Q: 没有真实设备数据，分析页面空白？**

分析页面 API 无数据时自动使用本地 CSV 兜底数据，应该能正常显示。
