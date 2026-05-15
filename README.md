# LogFlow

LogFlow 是一个面向 API 网关场景的访问日志采集与分析系统。

项目模拟后端服务接入 API 网关后产生的高频访问日志上报场景，采集接口路径、请求方法、状态码、响应耗时、客户端 ID、用户 ID、IP、User-Agent、trace_id 等访问日志字段，并提供访问量、错误率、P95 响应时间、慢请求、热门接口和错误事件等统计分析能力。

当前版本已完成 **FastAPI + MySQL 同步写入** 和 **基础统计分析接口增强**，用于先跑通最小可用链路：

```text
POST /api/events
  -> FastAPI 接收 API 网关访问日志
  -> SQLAlchemy 同步写入 MySQL
  -> MySQL 保存原始事件明细
  -> 统计接口基于 events 表进行聚合分析
```

后续版本将逐步接入 Redis 限流、Kafka 削峰、Consumer 异步落库和 Locust 压测。

> 本项目不是为了替代 ELK / Loki 等生产级可观测平台，而是用于验证高频日志上报场景下的限流、削峰、异步落库、统计查询和压测分析链路。

---

## 已完成功能

### Day 1：日志上报与基础后端链路

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

### Day 2：统计接口增强

- [x] `GET /api/stats/overview`：新增 `p95_duration_ms` 和 `slow_request_count`
- [x] `GET /api/stats/top-paths`：热门接口排行，包含访问量、平均耗时、错误数和错误率
- [x] `GET /api/stats/top-event-types`：事件类型排行
- [x] `GET /api/stats/slow-requests`：慢请求列表，支持阈值和数量限制
- [x] `GET /api/stats/errors`：错误事件统计，包含错误总数、错误率、错误路径排行和最近错误事件
- [x] 新增 `day2_smoke_test.ps1`，自动验证统计增强接口
- [x] 保持 Day 1 smoke test 兼容通过

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
│  │  ├─ day1_smoke_test.ps1
│  │  └─ day2_smoke_test.ps1
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

如果不想激活虚拟环境，也可以直接使用：

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

## 一键验收

确保 MySQL 和 FastAPI 都已启动后，执行 smoke test 脚本。

### Day 1 验收

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

验收结果示例：

```text
=== LogFlow Day 1 Smoke Test ===
Base URL: http://localhost:8000

[....] Health check [PASS]
[....] Create event (api_access) [PASS]
[....] Get event by event_id [PASS]
[....] Create event (api_error) [PASS]
[....] Create event (slow_request) [PASS]
[....] Stats overview [PASS]

  total_events     : 10
  total_clients    : 3
  total_users      : 3
  error_events     : 3
  error_rate       : 0.3
  avg_duration_ms  : 510.0
  top_paths        : [{"path":"/api/login","count":4},{"path":"/api/orders/create","count":3},{"path":"/api/payments/callback","count":3}]
  top_event_types  : [{"event_type":"api_access","count":4},{"event_type":"api_error","count":3},{"event_type":"slow_request","count":3}]
[....] Get nonexistent event (expect error) [PASS]

=== All Day 1 smoke tests passed ===
```

### Day 2 验收

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day2_smoke_test.ps1
```

脚本会自动验证：

```text
GET /api/stats/overview
GET /api/stats/top-paths
GET /api/stats/top-event-types
GET /api/stats/slow-requests
GET /api/stats/errors
```

验收结果示例：

```text
=== LogFlow Day 2 Smoke Test ===
Base URL: http://localhost:8000

[....] Insert test data [PASS]
[....] Stats overview [PASS]
[....] Top paths [PASS]
[....] Top event types [PASS]
[....] Slow requests [PASS]
[....] Errors [PASS]
[....] Slow requests (threshold_ms=300) [PASS]

=== All Day 2 smoke tests passed ===
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
p95_duration_ms
slow_request_count
top_paths
top_event_types
```

返回示例：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": {
    "total_events": 17,
    "total_clients": 9,
    "total_users": 9,
    "error_events": 5,
    "error_rate": 0.2941,
    "avg_duration_ms": 582.65,
    "p95_duration_ms": 2500.0,
    "slow_request_count": 5,
    "top_paths": [
      {
        "path": "/api/login",
        "count": 6
      },
      {
        "path": "/api/orders/create",
        "count": 5
      }
    ],
    "top_event_types": [
      {
        "event_type": "api_access",
        "count": 7
      },
      {
        "event_type": "api_error",
        "count": 5
      }
    ]
  },
  "request_id": "d936d5a6-945e-4002-aa3b-15c6949b5d73"
}
```

---

### 查询热门接口

```http
GET /api/stats/top-paths?limit=10
```

返回字段：

```text
path
count
avg_duration_ms
error_count
error_rate
```

---

### 查询事件类型排行

```http
GET /api/stats/top-event-types?limit=10
```

返回字段：

```text
event_type
count
avg_duration_ms
```

---

### 查询慢请求

```http
GET /api/stats/slow-requests?threshold_ms=1000&limit=10
```

返回字段：

```text
event_id
client_id
user_id
event_type
path
method
status_code
duration_ms
trace_id
created_at
```

---

### 查询错误事件统计

```http
GET /api/stats/errors?limit=10
```

返回字段：

```text
total_error_events
error_rate
top_error_paths
recent_errors
```

---

## 数据库说明

当前使用一张 `events` 表保存 API 网关访问日志。

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
- `user_id`：用户标识，可为空
- `event_type`：事件类型，例如 `api_access`、`api_error`、`slow_request`、`auth_failed`
- `path`：访问路径，例如 `/api/login`
- `method`：请求方法，例如 `GET`、`POST`
- `status_code`：接口状态码
- `duration_ms`：接口响应耗时
- `trace_id`：模拟网关或服务链路追踪 ID
- `request_id`：服务端为每次请求生成的请求 ID
- `extra`：扩展字段，当前以 JSON 字符串形式保存

---

## 统计规则

- 错误事件：`status_code >= 400`
- 错误率：`error_events / total_events`
- 慢请求：默认 `duration_ms >= 1000`
- 平均响应时间：基于 `duration_ms` 计算平均值，保留 2 位小数
- P95 响应时间：基于所有 `duration_ms` 排序后取 `ceil(0.95 * n) - 1` 位置的值
- 热门接口：按 path 出现次数降序
- 事件类型排行：按 event_type 出现次数降序

---

## Day 3-7 计划

> 以下功能尚未实现，仅作为后续开发路线。

- Day 3：Redis 限流与统计缓存，支持按 client_id / IP 限制高频请求
- Day 4：Kafka 异步削峰，将日志接收与 MySQL 落库解耦
- Day 5：工程化完善，补充结构化日志、pytest 测试、Docker Compose 多服务编排
- Day 6：Locust 压测，记录 100 / 300 / 500 并发下的 QPS、平均响应时间、P95 和错误率
- Day 7：README 完善、架构图、压测报告、简历描述和面试讲稿

---

## 项目边界

当前版本为学习与作品集项目，重点验证 API 网关访问日志采集场景下的后端链路设计。

目前已完成同步写入 MySQL 和统计查询能力，后续会逐步接入 Redis、Kafka 和 Locust 压测。

本项目不宣称支持百万级并发，也不替代 ELK、Loki、Prometheus、Grafana 等生产级可观测平台。
