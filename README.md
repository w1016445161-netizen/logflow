# LogFlow

LogFlow 是一个面向 API 网关场景的访问日志采集与分析系统。项目模拟后端服务接入 API 网关后产生的高频访问日志上报场景，采集接口路径、请求方法、状态码、响应耗时、客户端 ID、用户 ID、IP、User-Agent、trace_id 等字段，并提供统计查询、限流保护和异步削峰能力。

> 本项目用于验证高频日志上报场景下的限流、削峰、异步落库和统计查询链路，不替代 ELK / Loki / Prometheus / Grafana 等生产级可观测平台。

---

## 核心亮点

- **双模式写入**：支持 MySQL 同步写入和 Kafka 异步削峰两种模式，零代码切换，Kafka 不可用时自动 fallback。
- **多层保护**：固定窗口限流 + Redis 缓存 + 降级策略，所有中间件不可用时均自动放行，保证核心链路可用。
- **完整可观测**：结构化 JSON 日志、request_id 全链路追踪、请求耗时记录、业务异常分级。
- **可验证**：从基线到 Kafka 全链路的 smoke test、pytest 单元测试、Locust 压测脚本，确保每个模块可独立验收。

---

## 核心功能

- `POST /api/events` — 接收 API 网关访问日志并写入 MySQL 或 Kafka
- `GET /api/events/{event_id}` — 根据 event_id 查询单条日志
- `GET /api/stats/overview` — 统计概览（含 P95 响应时间、慢请求数量）
- `GET /api/stats/top-paths` — 按访问次数排行的路径统计
- `GET /api/stats/top-event-types` — 事件类型排行
- `GET /api/stats/slow-requests` — 慢请求查询
- `GET /api/stats/errors` — 错误汇总统计
- `GET /api/health` — 健康检查
- Redis 固定窗口限流（基于 client_id / IP）
- Redis 统计缓存（TTL 可配置，缓存不可用时自动降级查 MySQL）
- Kafka 异步削峰（Producer 写入 + Consumer 独立进程落库）
- 结构化 JSON 日志 + 请求耗时中间件 + 异常分级记录
- pytest mock 测试（统一响应、限流降级、缓存降级、写入模式切换）
- Locust 压测脚本（主链路 + 限流专项）

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
│  │  │  ├─ exceptions.py
│  │  │  └─ logging.py
│  │  ├─ db/
│  │  │  ├─ base.py
│  │  │  ├─ session.py
│  │  │  └─ models.py
│  │  ├─ kafka/
│  │  │  ├─ producer.py
│  │  │  └─ consumer.py
│  │  ├─ schemas/
│  │  │  └─ event.py
│  │  ├─ services/
│  │  │  ├─ event_service.py
│  │  │  ├─ stats_service.py
│  │  │  ├─ rate_limit_service.py
│  │  │  └─ cache_service.py
│  │  └─ main.py
│  ├─ locustfile.py
│  ├─ locustfile_rate_limit.py
│  ├─ scripts/
│  │  ├─ smoke_baseline.ps1
│  │  ├─ smoke_stats.ps1
│  │  ├─ smoke_redis.ps1
│  │  ├─ smoke_kafka.ps1
│  │  ├─ check_engineering.ps1
│  │  ├─ check_perf.ps1
│  │  └─ perf/
│  │     ├─ run_locust_100.ps1
│  │     ├─ run_locust_300.ps1
│  │     ├─ run_locust_500.ps1
│  │     └─ run_rate_limit_check.ps1
│  ├─ tests/
│  ├─ requirements.txt
│  └─ .env.example
├─ docs/
│  ├─ performance/
│  │  └─ locust_report_template.md
│  └─ images/
├─ docker-compose.yml
├─ .gitignore
└─ README.md
```

---

## 快速启动

### 1. 启动 Docker 服务

项目默认端口映射：

- MySQL 容器 `3306` → 宿主机 `3307`
- Redis 容器 `6379` → 宿主机 `6379`
- Kafka 容器 `9092` → 宿主机 `9092`

```powershell
cd D:\projects\logflow
docker compose up -d
```

正常应看到 `logflow-mysql`、`logflow-redis`、`logflow-kafka` 三个容器。

### 2. 创建虚拟环境

```powershell
cd D:\projects\logflow\backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. 安装依赖

```powershell
pip install -r requirements.txt
```

### 4. 创建 .env

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

### 5. 启动 FastAPI

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/api/health` 验证。

---

## 写入模式说明

默认 `EVENT_WRITE_MODE=sync`，所有请求同步写入 MySQL。

如需启用 Kafka 异步削峰：

1. 编辑 `backend/.env`，修改 `EVENT_WRITE_MODE=kafka`
2. 重启 FastAPI
3. 启动 Consumer：

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m app.kafka.consumer
```

Consumer 持续消费 Kafka 消息并写入 MySQL。Kafka 写入失败时自动 fallback 同步写库。

---

## 接口说明

### 健康检查

```http
GET /api/health
```

### 上报访问日志

```http
POST /api/events
```

| 字段 | 说明 |
|---|---|
| client_id | 客户端标识 |
| user_id | 用户 ID |
| event_type | 事件类型：`api_access`、`api_error`、`slow_request`、`auth_failed` |
| path | 访问路径 |
| method | HTTP 方法 |
| status_code | 响应状态码 |
| duration_ms | 响应耗时(毫秒) |
| ip | 客户端 IP |
| user_agent | User-Agent |
| service_name | 服务名称 |
| trace_id | 链路追踪 ID |
| extra | 扩展字段（JSON 对象） |

### 查询单条日志

```http
GET /api/events/{event_id}
```

### 统计接口

```http
GET /api/stats/overview
GET /api/stats/top-paths?limit=5
GET /api/stats/top-event-types?limit=5
GET /api/stats/slow-requests?threshold_ms=1000&limit=5
GET /api/stats/errors?limit=5
```

统一响应格式：

```json
{
  "success": true,
  "code": "OK",
  "message": "success",
  "data": { },
  "request_id": "6210f60d-89f4-4793-8808-f2c8f67be514"
}
```

---

## 数据库说明

使用 `events` 表保存 API 网关访问日志，主要字段：

`event_id` `client_id` `user_id` `event_type` `path` `method` `status_code` `duration_ms` `ip` `user_agent` `service_name` `trace_id` `extra` `request_id` `created_at`

- `event_id`：日志事件唯一 ID
- `trace_id`：模拟网关或服务链路追踪 ID
- `request_id`：服务端为每次请求生成的请求 ID
- `extra`：扩展字段，以 JSON 字符串形式保存

---

## Redis 设计

### 固定窗口限流

使用 `INCR` + `EXPIRE` 实现固定窗口限流。优先以 `client_id` 限流，无 `client_id` 时回落至 IP，均无时使用 anonymous 标记。限流不可用时（Redis 宕机或网络故障）自动放行，保证服务基本可用。

### 统计缓存

统计查询结果缓存到 Redis（TTL 可配置，默认 30s）。缓存命中直接返回，未命中查询 MySQL 后回填。Redis 不可用时自动降级查 MySQL，请求正常返回。

---

## Kafka 设计

### Producer

模块级延迟初始化 KafkaProducer（`acks=all`, `retries=3`, `linger_ms=5`），每次 `send_event_to_kafka` 同步等待 `future.get(timeout=10)` 确认写入成功。

### Consumer

独立 Python 进程，运行 `kafka-python` KafkaConsumer（`auto_offset_reset=latest`, `enable_auto_commit=True`）。消费流程：

1. 消费 JSON 消息，提取 event_id
2. 检查 event_id 是否已存在于 MySQL（幂等检查）
3. 不存在则写入 MySQL，打印 `[CONSUMED] event_id=...`
4. 已存在则跳过写入，打印 `[SKIPPED] duplicate event_id=...`
5. 处理失败时写入本地 dead letter 文件 `backend/dead_letters/kafka_failed_events.jsonl`

支持 `KeyboardInterrupt` 优雅退出。Dead letter 为本地 JSONL 文件，用于学习和故障排查；生产环境可扩展为 Kafka DLQ topic 或告警系统。

### Fallback 策略

当 `EVENT_WRITE_MODE=kafka` 但 Producer 故障或 Kafka broker 不可达时，`submit_event` 自动回退到同步写 MySQL（`write_mode=sync_fallback`），同时返回 `fallback_reason` 说明退避原因。

---

## 工程化能力

- **统一响应格式**：`{ success, code, message, data, request_id }`
- **request_id 全链路**：每个请求自动生成唯一 request_id，贯穿限流、日志、异常
- **结构化 JSON 日志**：每行一条 JSON，含 timestamp / level / request_id / method / path / status_code / duration_ms / client_ip
- **请求耗时日志**：中间件自动记录每个 HTTP 请求的耗时
- **异常日志**：业务异常（WARNING）和未预期异常（ERROR）均结构化记录
- **pytest mock 测试**：覆盖统一响应、限流降级、缓存降级、事件写入模式切换
- **Smoke test**：覆盖基线、统计、Redis、Kafka 全链路

### 运行测试

```powershell
cd D:\projects\logflow\backend

# pytest
.\.venv\Scripts\python.exe -m pytest -q

# 工程化检查
powershell -ExecutionPolicy Bypass -File .\scripts\check_engineering.ps1
```

---

## 测试与验收

确保 Docker 和 FastAPI 均已启动后，按顺序执行：

```powershell
cd D:\projects\logflow\backend

# 基线：健康检查 + 事件写入 + 单条查询 + 统计概览
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_baseline.ps1

# 统计：P95 / 慢请求 / 错误率 / 热门路径 / 事件类型
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_stats.ps1

# Redis：限流触发 + 缓存路径验证
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_redis.ps1

# Kafka：需要先设置 EVENT_WRITE_MODE=kafka 并启动 Consumer
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_kafka.ps1
```

---

## Locust 压测

### 脚本说明

| 脚本 | 用途 |
|---|---|
| [backend/locustfile.py](backend/locustfile.py) | 主链路压测，使用随机 client_id 避免限流干扰 |
| [backend/locustfile_rate_limit.py](backend/locustfile_rate_limit.py) | 限流专项，使用固定 client_id 验证限流保护 |

主压测任务权重：POST /api/events（10）、GET /api/stats/overview（1）、GET /api/stats/top-paths（1）。

限流专项中所有虚拟用户使用相同 client_id，429 为预期行为，不标记失败。

### 快速检查

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\check_perf.ps1
```

### 正式压测

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_100.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_300.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_500.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_rate_limit_check.ps1
```

CSV 结果输出到 `docs/performance/`。压测报告模板见 [docs/performance/locust_report_template.md](docs/performance/locust_report_template.md)，所有性能数据需实际运行后填入。

### 压测结果

| 模式 | 并发数 | Spawn Rate | 时长 | RPS/QPS | 平均响应时间(ms) | P95(ms) | 错误率 | 备注 |
|---|---:|---:|---:|---:|---:|---:|---|
| sync | 100 | 10/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | |
| sync | 300 | 30/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | |
| sync | 500 | 50/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | |
| kafka | 100 | 10/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | Consumer 已启动 |
| kafka | 300 | 30/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | Consumer 已启动 |
| kafka | 500 | 50/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | Consumer 已启动 |

### Redis 限流专项

| 测试项 | 并发数 | 时长 | 是否出现 429 | 非预期错误率 | 备注 |
|---|---:|---:|---|---|
| 固定 client_id 限流测试 | 50 | 1m | 待填写 | 待填写 | 429 为预期行为 |

---

## 开发里程碑

| 阶段 | 内容 |
|---|---|
| 基础链路 | FastAPI + MySQL 日志上报与查询、健康检查、统一响应格式 |
| 统计分析 | P95 响应时间、慢请求统计、错误率、热门接口排行 |
| Redis 增强 | 固定窗口限流、统计缓存、Redis 不可用自动降级 |
| Kafka 异步化 | Producer 写入 + Consumer 独立进程落库、幂等检查、dead letter 记录、sync/kafka 模式切换、写入失败 fallback |
| 工程化 | 结构化 JSON 日志、请求耗时中间件、异常分级、pytest mock 测试、smoke test |
| 压测准备 | Locust 主链路压测脚本、限流专项脚本、压测报告模板 |

---

## 项目边界与后续优化

当前版本重点验证 API 网关访问日志采集场景下的后端链路设计。在 macOS / Windows 本地 Docker 环境中可正常运行全部功能。

**已有约束：**

- 限流为固定窗口实现，非滑动窗口。
- Consumer 为逐条消费落库，未做批量写入优化。已支持基于 event_id 的幂等写入检查。
- 单条消息处理失败时写入本地 dead letter JSONL 文件，Consumer 不退出。
- 缓存存在 TTL 内短暂延迟。
- 不宣称支持百万级并发。
- 不替代 ELK、Loki、Prometheus、Grafana 等生产级可观测平台。

**后续优化方向：**

- 批量落库：Consumer 攒批写入 MySQL，减少 DB 连接开销
- 滑动窗口限流：使用 sorted set 替代固定窗口
- Consumer 消费延迟监控
