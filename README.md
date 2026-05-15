# LogFlow

LogFlow 是一个面向 API 网关场景的访问日志采集与分析系统。

项目模拟后端服务接入 API 网关后产生的高频访问日志上报场景，采集接口路径、请求方法、状态码、响应耗时、客户端 ID、用户 ID、IP、User-Agent、trace_id 等访问日志字段，并提供基础统计查询能力。

Day 1 当前实现的是 **FastAPI + MySQL 同步写入版本**，用于先跑通最小可用链路：

```text
POST /api/events
  -> FastAPI 接收 API 网关访问日志
  -> SQLAlchemy 同步写入 MySQL
  -> 返回 event_id 和 request_id
```

后续版本将逐步接入 Redis 限流、Kafka 削峰、Consumer 异步落库和 Locust 压测。

> 本项目不是为了替代 ELK / Loki 等生产级可观测平台，而是用于验证高频日志上报场景下的限流、削峰、异步落库和统计查询链路。

---

## Day 1 已完成

- [x] FastAPI + MySQL 同步写入
- [x] `POST /api/events`：接收 API 网关访问日志并写入 MySQL
- [x] `GET /api/events/{event_id}`：根据 event_id 查询单条日志
- [x] `GET /api/stats/overview`：查询基础统计数据
- [x] `GET /api/health`：健康检查
- [x] 统一响应格式：`success / code / message / data / request_id`
- [x] request_id 请求链路标识
- [x] Docker Compose 启动 MySQL 8.0
- [x] 应用启动时自动创建数据表
- [x] PowerShell smoke test 脚本验证核心链路

---

## 技术栈

- FastAPI
- SQLAlchemy
- MySQL 8.0
- PyMySQL
- Pydantic Settings
- Docker Compose
- PowerShell Smoke Test

---

## 项目结构

```text
logflow/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  │  ├─ router.py
│  │  │  └─ routes/
│  │  │     ├─ health.py
│  │  │     ├─ events.py
│  │  │     └─ stats.py
│  │  ├─ core/
│  │  │  ├─ config.py
│  │  │  ├─ response.py
│  │  │  └─ exceptions.py
│  │  ├─ db/
│  │  │  ├─ base.py
│  │  │  ├─ session.py
│  │  │  └─ models.py
│  │  ├─ schemas/
│  │  │  └─ event.py
│  │  ├─ services/
│  │  │  ├─ event_service.py
│  │  │  └─ stats_service.py
│  │  └─ main.py
│  ├─ scripts/
│  │  └─ day1_smoke_test.ps1
│  ├─ requirements.txt
│  └─ .env.example
├─ docs/
│  └─ images/
├─ docker-compose.yml
├─ README.md
├─ CLAUDE.md
└─ .gitignore
```

---

## 快速启动

### 1. 启动 MySQL

项目默认将容器内 MySQL 的 `3306` 端口映射到本机 `3307`，避免和本机已有 MySQL 冲突。

```powershell
cd D:\projects\logflow
docker compose up -d
```

检查容器状态：

```powershell
docker ps
```

正常应看到类似结果：

```text
logflow-mysql   0.0.0.0:3307->3306/tcp
```

如果想查看 MySQL 是否初始化完成：

```powershell
docker logs logflow-mysql --tail 50
```

看到 `ready for connections` 表示 MySQL 已经可以连接。

---

### 2. 创建 Python 虚拟环境

```powershell
cd D:\projects\logflow\backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

---

### 4. 创建 `.env`

```powershell
copy .env.example .env
```

`.env` 示例：

```env
APP_NAME=LogFlow
APP_ENV=dev
DATABASE_URL=mysql+pymysql://logflow:logflow123@localhost:3307/logflow
```

---

### 5. 启动 FastAPI

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动成功后访问：

```text
http://localhost:8000/api/health
```

---

## 一键验收 Day 1

确保 MySQL 和 FastAPI 都已启动后，执行：

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day1_smoke_test.ps1
```

脚本会自动验证：

```text
GET  /api/health
POST /api/events
GET  /api/events/{event_id}
POST /api/events api_error
POST /api/events slow_request
GET  /api/stats/overview
GET  /api/events/nonexistent
```

当前 Day 1 验收结果示例：

```text
=== LogFlow Day 1 Smoke Test ===
Base URL: http://localhost:8000

[....] Health check [PASS]
[....] Create event (api_access) [PASS]
[....] Get event by event_id [PASS]
[....] Create event (api_error) [PASS]
[....] Create event (slow_request) [PASS]
[....] Stats overview [PASS]

  total_events     : 4
  total_clients    : 3
  total_users      : 3
  error_events     : 1
  error_rate       : 0.25
  avg_duration_ms  : 432.5
  top_paths        : [{"path":"/api/login","count":2},{"path":"/api/orders/create","count":1},{"path":"/api/payments/callback","count":1}]
  top_event_types  : [{"event_type":"api_access","count":2},{"event_type":"api_error","count":1},{"event_type":"slow_request","count":1}]
[....] Get nonexistent event (expect error) [PASS]

=== All Day 1 smoke tests passed ===
```

---

## 接口说明

### 健康检查

```http
GET /api/health
```

返回示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "status": "ok",
    "service": "LogFlow"
  },
  "request_id": "6210f60d-89f4-4793-8808-f2c8f67be514"
}
```

---

### 上报访问日志

```http
POST /api/events
```

请求体示例：

```json
{
  "client_id": "client-001",
  "user_id": "u10001",
  "event_type": "api_access",
  "path": "/api/login",
  "method": "POST",
  "status_code": 200,
  "duration_ms": 45,
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0",
  "service_name": "gateway-service",
  "trace_id": "trace-demo-001",
  "extra": {
    "login_type": "password"
  }
}
```

PowerShell 测试方式：

```powershell
$body = @{
  client_id = "client-001"
  user_id = "u10001"
  event_type = "api_access"
  path = "/api/login"
  method = "POST"
  status_code = 200
  duration_ms = 45
  ip = "192.168.1.100"
  user_agent = "Mozilla/5.0"
  service_name = "gateway-service"
  trace_id = "trace-demo-001"
  extra = @{
    login_type = "password"
  }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
  -Uri "http://localhost:8000/api/events" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

---

### 查询单条日志

```http
GET /api/events/{event_id}
```

---

### 查询统计概览

```http
GET /api/stats/overview
```

当前返回字段：

```text
total_events
total_clients
total_users
error_events
error_rate
avg_duration_ms
top_paths
top_event_types
```

---

## 数据库说明

Day 1 当前使用一张 `events` 表保存 API 网关访问日志。

主要字段包括：

```text
id
event_id
client_id
user_id
event_type
path
method
status_code
duration_ms
ip
user_agent
service_name
trace_id
extra
request_id
created_at
```

其中：

- `event_id`：日志事件唯一 ID
- `client_id`：客户端标识
- `event_type`：事件类型，例如 `api_access`、`api_error`、`slow_request`
- `path`：访问路径，例如 `/api/login`
- `status_code`：接口状态码
- `duration_ms`：接口响应耗时
- `trace_id`：模拟网关或服务链路追踪 ID
- `request_id`：服务端为每次请求生成的请求 ID
- `extra`：扩展字段，当前以 JSON 字符串形式保存

---

## Day 2-7 计划

> 以下功能尚未实现，仅作为后续开发路线。

- Day 2：统计接口增强，补充 P95 响应时间、慢请求排行、错误事件统计、热门接口 Top N
- Day 3：Redis 限流与统计缓存，支持按 client_id / IP 限制高频请求
- Day 4：Kafka 异步削峰，将日志接收与 MySQL 落库解耦
- Day 5：工程化完善，补充结构化日志、pytest 测试、Docker Compose 多服务编排
- Day 6：Locust 压测，记录 100 / 300 / 500 并发下的 QPS、平均响应时间、P95 和错误率
- Day 7：README 完善、架构图、压测报告、简历描述和面试讲稿

---

## 项目边界

当前版本为学习与作品集项目，重点验证 API 网关访问日志采集场景下的后端链路设计。

Day 1 仅实现同步写入 MySQL 的最小可用版本，后续会逐步接入 Redis、Kafka 和 Locust 压测。

本项目不宣称支持百万级并发，也不替代 ELK、Loki、Prometheus、Grafana 等生产级可观测平台。