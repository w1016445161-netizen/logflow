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

### Day 2 已完成

- [x] `GET /api/stats/overview` 增强：`p95_duration_ms`、`slow_request_count`
- [x] `GET /api/stats/top-paths`：按访问次数排行的路径统计
- [x] `GET /api/stats/top-event-types`：事件类型排行
- [x] `GET /api/stats/slow-requests`：慢请求查询
- [x] `GET /api/stats/errors`：错误汇总统计
- [x] Day 2 smoke test

### Day 3 已完成

- [x] Redis 服务接入（Docker Compose 启动 redis:7）
- [x] `POST /api/events` 基于 client_id / IP 的固定窗口限流
- [x] 统计接口 Redis 缓存（TTL 可配置，缓存不可用时自动降级查 MySQL）
- [x] 限流不可用时自动放行，保证服务基本可用
- [x] Day 3 smoke test

### Day 4 已完成

- [x] Kafka 服务接入（Docker Compose 启动 apache/kafka:3.7.0，KRaft 模式）
- [x] `EVENT_WRITE_MODE` 支持 `sync` / `kafka` 写入模式切换
- [x] FastAPI Producer 写入 Kafka topic `logflow-events`
- [x] Consumer 独立进程异步消费并写入 MySQL
- [x] Kafka 写入失败时自动 fallback 同步写库
- [x] Day 4 smoke test

### Day 5 已完成

- [x] 结构化 JSON 日志（Python 标准 logging，JsonFormatter）
- [x] 请求耗时日志（中间件记录 method / path / status / duration / request_id / client_ip）
- [x] 异常日志（AppException 输出 WARNING，未预期异常输出 ERROR）
- [x] pytest mock 测试（统一响应、限流、缓存、事件写入模式切换）
- [x] Day 5 工程化检查脚本

### Day 6 已完成

- [x] Locust 主链路压测脚本（backend/locustfile.py）
- [x] Redis 限流专项压测脚本（backend/locustfile_rate_limit.py）
- [x] 100 / 300 / 500 并发压测命令封装（backend/scripts/perf/）
- [x] 限流检查脚本（backend/scripts/perf/run_rate_limit_check.ps1）
- [x] 压测报告模板（docs/performance/day6_locust_report.md）
- [x] Day 6 perf check 快速检查脚本

---

## 技术栈

- FastAPI
- SQLAlchemy
- MySQL 8.0
- PyMySQL
- Pydantic Settings
- Redis 7
- Kafka (Apache 3.7.0, KRaft)
- Docker Compose
- pytest
- Locust
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
│  ├─ locustfile.py
│  ├─ locustfile_rate_limit.py
│  ├─ scripts/
│  │  ├─ day1_smoke_test.ps1
│  │  ├─ day2_smoke_test.ps1
│  │  ├─ day3_smoke_test.ps1
│  │  ├─ day4_smoke_test.ps1
│  │  ├─ day5_engineering_check.ps1
│  │  ├─ day6_perf_check.ps1
│  │  └─ perf/
│  │     ├─ run_locust_100.ps1
│  │     ├─ run_locust_300.ps1
│  │     ├─ run_locust_500.ps1
│  │     └─ run_rate_limit_check.ps1
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

项目默认将容器内 MySQL 的 `3306` 端口映射到本机 `3307`，避免和本机已有 MySQL 冲突。Redis 映射到本机 `6379`，Kafka 映射到本机 `9092`。

```powershell
cd D:\projects\logflow
docker compose up -d
```

检查容器状态：

```powershell
docker ps
```

正常应看到 `logflow-mysql`、`logflow-redis`、`logflow-kafka` 三个容器。

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
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
STATS_CACHE_TTL_SECONDS=30
EVENT_WRITE_MODE=sync
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC_EVENTS=logflow-events
KAFKA_PRODUCER_ENABLED=true
KAFKA_CONSUMER_GROUP=logflow-consumer-group
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

### 6. 切换到 Kafka 模式（可选）

默认 `EVENT_WRITE_MODE=sync`，所有请求同步写入 MySQL。

如需启用 Kafka 异步削峰：

编辑 `backend/.env`，修改：

```env
EVENT_WRITE_MODE=kafka
```

重启 FastAPI，然后启动 Consumer：

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m app.kafka.consumer
```

Consumer 会持续消费 Kafka 消息并写入 MySQL。Kafka 写入失败时自动 fallback 同步写库。

---

## 工程化能力

- **统一响应格式**：`{ success, code, message, data, request_id }`
- **request_id 全链路**：每个请求自动生成唯一 request_id，贯穿限流、日志、异常
- **结构化 JSON 日志**：每行一条 JSON，含 timestamp / level / request_id / method / path / status_code / duration_ms / client_ip
- **请求耗时日志**：中间件自动记录每个 HTTP 请求的耗时
- **异常日志**：业务异常（WARNING）和未预期异常（ERROR）均结构化记录
- **pytest mock 测试**：覆盖统一响应、限流降级、缓存降级、事件写入模式切换
- **Smoke test**：Day 1-4 各级别 PowerShell 烟雾测试
- **Docker Compose**：统一管理 MySQL、Redis、Kafka 服务

### 运行测试

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m pytest -q
```

或使用 Day 5 工程化检查脚本：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\day5_engineering_check.ps1
```

---

## 压测说明

### 主链路压测

主压测脚本 [backend/locustfile.py](backend/locustfile.py) 使用**随机 client_id**，避免触发 Redis 限流对主链路指标产生干扰。

- POST /api/events（权重 10）—— 高频日志上报
- GET /api/stats/overview（权重 1）—— 统计概览查询
- GET /api/stats/top-paths?limit=5（权重 1）—— 热门路径查询

所有请求检查 JSON `success` 字段。429 出现在主压测中视为异常。`sync_fallback` 不标记失败，但如果出现则需要在报告中说明 Kafka producer 不可用。

### 限流专项压测

限流专项脚本 [backend/locustfile_rate_limit.py](backend/locustfile_rate_limit.py) 所有虚拟用户使用**固定 client_id** `rate-limit-load-test`，高频发送 POST /api/events。

**429 是预期行为**，脚本将其标记为 success。其他 4xx/5xx 或 `success=false` 才视为失败。

### 运行压测

确保 Docker（MySQL、Redis、Kafka）和 FastAPI 均已启动后：

```powershell
cd D:\projects\logflow\backend

# 快速检查（15 秒验证链路是否正常）
powershell -ExecutionPolicy Bypass -File .\scripts\day6_perf_check.ps1

# 正式压测
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_100.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_300.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_500.ps1

# 限流专项
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_rate_limit_check.ps1
```

CSV 结果输出到 [docs/performance/](docs/performance/)。压测报告模板见 [docs/performance/day6_locust_report.md](docs/performance/day6_locust_report.md)。

> 报告模板中所有性能数据均为"待填写"，请在实际运行压测后填入结果。

---

## 一键验收

确保 MySQL 和 FastAPI 都已启动后，执行：

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day1_smoke_test.ps1
```

脚本会自动验证 Day 1 核心链路。

### Day 2 验收

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day2_smoke_test.ps1
```

### Day 3 验收

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day3_smoke_test.ps1
```

### Day 4 验收（Kafka 模式）

确保 `.env` 中 `EVENT_WRITE_MODE=kafka`，重启 FastAPI 后：

```powershell
# 终端 1：启动 Consumer
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m app.kafka.consumer

# 终端 2：运行 smoke test
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day4_smoke_test.ps1
```

### Day 5 验收

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day5_engineering_check.ps1
```

### Day 6 验收

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\day6_perf_check.ps1
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

## Day 7 计划

> 以下功能尚未实现，仅作为后续开发路线。

- Day 7：README 完善、架构图、压测报告、简历描述和面试讲稿

---

## 项目边界

当前版本为学习与作品集项目，重点验证 API 网关访问日志采集场景下的后端链路设计。

目前已实现：FastAPI 同步写入 MySQL、统计查询、Redis 固定窗口限流、统计缓存、Kafka 异步削峰、Consumer 异步落库、Locust 压测。

缓存存在 TTL 内短暂延迟，限流不可用时自动放行。Consumer 为逐条消费落库，Kafka 写入失败时支持 fallback 同步写库。

本项目不宣称支持百万级并发，也不替代 ELK、Loki、Prometheus、Grafana 等生产级可观测平台。