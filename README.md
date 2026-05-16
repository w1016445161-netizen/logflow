# LogFlow

LogFlow 是一个面向 **API 网关访问日志场景** 的日志采集与分析系统。

项目模拟后端服务接入 API 网关后产生的高频访问日志上报场景，采集接口路径、请求方法、状态码、响应耗时、客户端 ID、用户 ID、IP、User-Agent、trace_id 等字段，并提供日志上报、Redis 限流、Kafka 削峰、Consumer 异步落库、MySQL 明细存储、统计查询、Redis 缓存、结构化日志、pytest 测试和 Locust 压测能力。

> 本项目用于验证高频日志上报场景下的限流、削峰、异步落库和统计查询链路，不替代 ELK / Loki / Prometheus / Grafana 等生产级可观测平台，也不宣称支持百万级并发。

---

## 项目亮点

- **双模式写入**：支持 MySQL 同步写入和 Kafka 异步削峰两种模式，通过 `EVENT_WRITE_MODE=sync / kafka` 切换；Kafka 不可用时自动 fallback 到同步写库。
- **Redis 限流与缓存**：基于 `client_id / IP` 实现固定窗口限流，并对统计接口结果进行 TTL 缓存；Redis 异常时自动降级，保证核心链路可用。
- **Kafka 异步落库**：FastAPI Producer 写入 Kafka 后快速返回，Consumer 独立进程异步消费并写入 MySQL，支持 event_id 幂等检查和本地 dead letter 失败记录。
- **工程化完整**：统一响应格式、request_id、结构化 JSON 日志、请求耗时中间件、异常分级、pytest mock 测试、PowerShell smoke test、Locust 压测脚本均已接入。
- **压测可解释**：通过 mixed workload、ingest-only 和 rate-limit-check 三类压测，分别验证混合负载、纯写入链路和 Redis 限流能力，并记录瓶颈分析。

---

## 架构设计

```mermaid
flowchart LR
    Client[Client / Locust] --> API[FastAPI<br/>POST /api/events]

    API --> RL[Redis Rate Limit<br/>client_id / IP]
    RL --> Mode{EVENT_WRITE_MODE}

    Mode -->|sync| MySQL[(MySQL<br/>events)]
    Mode -->|kafka| Producer[Kafka Producer]
    Producer --> Kafka[(Kafka<br/>logflow-events)]
    Kafka --> Consumer[Consumer Process]
    Consumer --> MySQL

    API --> Stats[Stats APIs]
    Stats --> Cache[Redis Stats Cache]
    Cache --> MySQL

    API --> Logs[Structured JSON Logs]
```

---

## 核心功能

| 模块 | 功能 |
|---|---|
| 日志上报 | `POST /api/events` 接收 API 网关访问日志 |
| 单条查询 | `GET /api/events/{event_id}` 根据 event_id 查询单条日志 |
| 统计总览 | `GET /api/stats/overview` 查询总量、错误率、平均耗时、P95、慢请求数量 |
| 热门路径 | `GET /api/stats/top-paths` 查询访问量最高的接口路径 |
| 事件类型排行 | `GET /api/stats/top-event-types` 查询事件类型分布 |
| 慢请求分析 | `GET /api/stats/slow-requests` 查询超过阈值的慢请求 |
| 错误事件统计 | `GET /api/stats/errors` 查询错误数量、错误率、错误路径排行和最近错误 |
| Redis 限流 | 基于 `client_id / IP` 的固定窗口限流 |
| Redis 缓存 | 对统计接口结果进行 TTL 缓存 |
| Kafka 削峰 | `EVENT_WRITE_MODE=kafka` 时日志先写入 Kafka |
| Consumer 落库 | 独立 Consumer 进程消费 Kafka 消息并写入 MySQL |
| 消费幂等 | Consumer 写库前基于 event_id 检查是否重复 |
| Dead letter | 单条消息处理失败时写入本地 JSONL 文件 |
| fallback | Kafka 写入失败时 fallback 到同步写库 |
| 工程化 | 统一响应、request_id、结构化 JSON 日志、异常日志 |
| 测试 | pytest mock 测试 + PowerShell smoke test |
| 压测 | Locust mixed workload、ingest-only、Redis 限流专项压测 |

---

## 技术栈

| 类型 | 技术 |
|---|---|
| Web 框架 | FastAPI |
| ORM | SQLAlchemy |
| 数据库 | MySQL 8.0 |
| MySQL Driver | PyMySQL |
| 配置管理 | Pydantic Settings |
| 缓存 / 限流 | Redis 7 |
| 消息队列 | Apache Kafka 3.7.0, KRaft |
| Kafka Client | kafka-python |
| 容器编排 | Docker Compose |
| 日志 | Python logging + JSON Formatter |
| 测试 | pytest, httpx |
| 压测 | Locust |
| 脚本 | PowerShell |

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
│  │  │  ├─ redis_client.py
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
│  ├─ locustfile_ingest_only.py
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
│  │     ├─ run_ingest_300.ps1
│  │     ├─ run_ingest_500.ps1
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

### 1. 启动基础服务

项目通过 Docker Compose 启动 MySQL、Redis 和 Kafka。

```powershell
cd D:\projects\logflow
docker compose up -d
docker ps
```

端口说明：

| 服务 | 容器端口 | 宿主机端口 |
|---|---:|---:|
| MySQL | 3306 | 3307 |
| Redis | 6379 | 6379 |
| Kafka | 9092 | 9092 |
| FastAPI | 8000 | 8000 |

> MySQL 容器内部端口是 `3306`，宿主机访问端口是 `3307`，避免和本机已有 MySQL 冲突。

---

### 2. 创建虚拟环境

```powershell
cd D:\projects\logflow\backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

### 3. 安装依赖

```powershell
cd D:\projects\logflow\backend
pip install -r requirements.txt
```

---

### 4. 创建 `.env`

```powershell
cd D:\projects\logflow\backend
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

开发调试：

```powershell
cd D:\projects\logflow\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

压测时建议不要使用 `--reload`：

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

健康检查：

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET
```

---

## 写入模式

### sync 模式

默认写入模式为 `sync`：

```env
EVENT_WRITE_MODE=sync
```

链路：

```text
POST /api/events
  -> Redis 限流
  -> 同步写入 MySQL
  -> 返回 event_id
```

---

### kafka 模式

修改 `.env`：

```env
EVENT_WRITE_MODE=kafka
```

重启 FastAPI 后，启动 Consumer：

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m app.kafka.consumer
```

链路：

```text
POST /api/events
  -> Redis 限流
  -> Kafka Producer 写入 Kafka
  -> 接口快速返回 event_id
  -> Consumer 异步消费
  -> MySQL 落库
```

如果 Kafka 写入失败，系统会 fallback 到同步写库，并返回 `write_mode=sync_fallback` 和 `fallback_reason`。

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

主要字段：

| 字段 | 说明 |
|---|---|
| client_id | 客户端标识 |
| user_id | 用户 ID |
| event_type | 事件类型，如 `api_access`、`api_error`、`slow_request`、`auth_failed` |
| path | 访问路径 |
| method | HTTP 方法 |
| status_code | 响应状态码 |
| duration_ms | 响应耗时，单位毫秒 |
| ip | 客户端 IP |
| user_agent | User-Agent |
| service_name | 服务名称 |
| trace_id | 链路追踪 ID |
| extra | 扩展字段，JSON 对象 |

---

### 查询单条日志

```http
GET /api/events/{event_id}
```

---

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
  "data": {},
  "request_id": "6210f60d-89f4-4793-8808-f2c8f67be514"
}
```

---

## 数据库说明

使用 `events` 表保存 API 网关访问日志，主要字段：

```text
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

字段说明：

| 字段 | 说明 |
|---|---|
| event_id | 日志事件唯一 ID |
| trace_id | 模拟网关或服务链路追踪 ID |
| request_id | 服务端为每次请求生成的请求 ID |
| extra | 扩展字段，以 JSON 字符串形式保存 |
| created_at | 日志创建时间 |

---

## Redis 设计

### 固定窗口限流

使用 `INCR` + `EXPIRE` 实现固定窗口限流。

限流维度：

```text
client_id 优先
  -> 没有 client_id 时使用 IP
  -> 都没有时使用 anonymous
```

默认配置：

```env
RATE_LIMIT_ENABLED=true
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60
```

Redis 不可用时，限流逻辑会降级为放行，避免 Redis 故障导致核心接口不可用。

---

### 统计缓存

统计查询结果缓存到 Redis，TTL 可配置：

```env
STATS_CACHE_TTL_SECONDS=30
```

缓存命中时直接返回，未命中时查询 MySQL 后回填。Redis 不可用时自动降级为查询 MySQL。

---

## Kafka 设计

### Producer

Producer 使用模块级懒加载单例，首次写入时初始化 KafkaProducer。

当前配置包括：

```text
acks=all
retries=3
linger_ms=5
```

写入时通过 `future.get(timeout=10)` 等待 Kafka 确认。FastAPI 应用退出时会主动 `flush()` 并关闭 Producer 连接。

---

### Consumer

Consumer 是独立 Python 进程，不嵌入 FastAPI 生命周期。

启动方式：

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m app.kafka.consumer
```

消费流程：

```text
消费 Kafka 消息
  -> 提取 event_id
  -> 查询 MySQL 判断 event_id 是否已存在
  -> 不存在则写入 MySQL
  -> 已存在则跳过
  -> 单条消息处理失败时写入 dead letter JSONL
```

重复消息会输出：

```text
[SKIPPED] duplicate event_id=...
```

成功消费会输出：

```text
[CONSUMED] event_id=...
```

失败消息会写入：

```text
backend/dead_letters/kafka_failed_events.jsonl
```

Dead letter 当前为本地 JSONL 文件，用于学习项目中的失败排查；生产环境可扩展为 Kafka DLQ Topic 或告警系统。

---

## 工程化能力

| 能力 | 说明 |
|---|---|
| 统一响应 | 所有接口统一返回 `success / code / message / data / request_id` |
| request_id | 每个请求自动生成 request_id，用于链路追踪 |
| 结构化日志 | 使用 Python logging 输出 JSON 格式日志 |
| 请求耗时 | 记录 method、path、status_code、duration_ms、client_ip |
| 异常处理 | 统一处理业务异常和未知异常，不向 API 响应暴露 traceback |
| pytest | mock 测试限流、缓存、写入模式、dead letter、消费幂等 |
| smoke test | PowerShell 脚本验证基线、统计、Redis、Kafka 链路 |
| Docker Compose | 一键启动 MySQL、Redis、Kafka |
| Locust | 支持混合负载、纯写入和限流专项压测 |

---

## 测试与验收

### pytest

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m pytest -q
```

### smoke test

确保 Docker 和 FastAPI 均已启动后执行：

```powershell
cd D:\projects\logflow\backend

# 基线：健康检查 + 事件写入 + 单条查询 + 统计概览
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_baseline.ps1

# 统计：P95 / 慢请求 / 错误率 / 热门路径 / 事件类型
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_stats.ps1

# Redis：限流触发 + 缓存路径验证
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_redis.ps1

# 工程化检查
powershell -ExecutionPolicy Bypass -File .\scripts\check_engineering.ps1
```

Kafka smoke test 需要先切换到 kafka 模式并启动 Consumer：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_kafka.ps1
```

---

## Locust 压测

### 脚本说明

| 脚本 | 用途 |
|---|---|
| [backend/locustfile.py](backend/locustfile.py) | Mixed workload 压测，同时压测写入和统计查询，使用随机 client_id 避免限流干扰 |
| [backend/locustfile_ingest_only.py](backend/locustfile_ingest_only.py) | Ingest-only 纯写入压测，只压测 `POST /api/events`，排除统计接口干扰 |
| [backend/locustfile_rate_limit.py](backend/locustfile_rate_limit.py) | 限流专项，使用固定 client_id 验证 Redis 固定窗口限流 |

Mixed workload 任务权重：

```text
POST /api/events          10
GET /api/stats/overview   1
GET /api/stats/top-paths  1
```

Ingest-only 只包含 `POST /api/events` 单一任务，用于观察日志上报主链路在 sync / kafka 模式下的吞吐和延迟。

限流专项中所有虚拟用户使用相同 client_id，429 为预期行为，不标记为失败。

---

### 快速检查

```powershell
cd D:\projects\logflow\backend
powershell -ExecutionPolicy Bypass -File .\scripts\check_perf.ps1
```

---

### 正式压测命令

```powershell
cd D:\projects\logflow\backend

# mixed workload
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_100.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_300.ps1

# ingest-only
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_ingest_300.ps1

# rate-limit-check
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_rate_limit_check.ps1
```

CSV 结果默认输出到：

```text
docs/performance/
```

完整压测报告见：

```text
docs/performance/locust_report_template.md
```

---

## 压测结果摘要

压测环境为本机 Windows + Docker Desktop，FastAPI 本机运行，MySQL / Redis / Kafka 通过 Docker Compose 启动。

本项目进行了三类压测：

- **mixed workload**：同时压测日志上报接口和统计查询接口，用于观察写入与查询并存时的系统表现。
- **ingest-only**：只压测 `POST /api/events`，用于观察日志上报主链路性能。
- **rate-limit-check**：使用固定 client_id 高频请求，用于验证 Redis 固定窗口限流能力。

### mixed workload

| 场景 | 模式 | 并发数 | RPS/QPS | 平均响应时间(ms) | P95(ms) | 错误率 |
|---|---|---:|---:|---:|---:|---:|
| mixed workload | sync | 100 | 307.32 | 279.78 | 420 | 0.00% |
| mixed workload | sync | 300 | 195.20 | 1435.46 | 1700 | 0.00% |
| mixed workload | kafka | 100 | 368.12 | 219.91 | 260 | 0.00% |
| mixed workload | kafka | 300 | 227.65 | 1234.08 | 3100 | 0.07% |

在 300 并发 mixed workload 场景下，kafka 模式出现少量失败，失败集中在 `GET /api/stats/overview`，`POST /api/events` 未出现失败。这说明当前瓶颈主要在实时统计查询，而不是日志上报接口。

### ingest-only

| 场景 | 模式 | 并发数 | RPS/QPS | 平均响应时间(ms) | P95(ms) | 错误率 |
|---|---|---:|---:|---:|---:|---:|
| ingest-only | sync | 300 | 313.02 | 894.03 | 1100 | 0.00% |
| ingest-only | kafka | 300 | 603.45 | 455.01 | 550 | 0.00% |

在 300 并发 ingest-only 场景下，Kafka 异步写入相比同步写库将 RPS 从 313.02 提升到 603.45，平均响应时间从 894.03ms 降至 455.01ms，P95 从 1100ms 降至 550ms，错误率保持 0.00%。

### Redis 限流专项

| 测试项 | 并发数 | 时长 | 请求数 | 平均响应时间(ms) | P95(ms) | 非预期错误率 | 说明 |
|---|---:|---:|---:|---:|---:|---:|---|
| 固定 client_id 限流测试 | 50 | 1m | 34146 | 62.97 | 82 | 0.00% | 429 为预期行为 |

Redis 限流专项测试使用固定 client_id 高频请求，超过固定窗口阈值后会返回 429。压测脚本将 429 视为预期行为，因此非预期错误率为 0.00%，说明限流链路可以稳定保护异常高频客户端。

---

## 开发里程碑

| 阶段 | 内容 |
|---|---|
| 基础链路 | FastAPI + MySQL 日志上报与查询、健康检查、统一响应格式 |
| 统计分析 | P95 响应时间、慢请求统计、错误率、热门接口排行 |
| Redis 增强 | 固定窗口限流、统计缓存、Redis 不可用自动降级 |
| Kafka 异步化 | Producer 写入 + Consumer 独立进程落库、幂等检查、dead letter 记录、sync/kafka 模式切换、写入失败 fallback |
| 工程化 | 结构化 JSON 日志、请求耗时中间件、异常分级、pytest mock 测试、smoke test |
| 压测分析 | Locust mixed workload、ingest-only、Redis 限流专项压测，分析同步写库、Kafka 异步写入和实时统计瓶颈 |

---

## 项目边界与后续优化

当前版本重点验证 API 网关访问日志采集场景下的后端链路设计，属于学习与作品集项目。

### 已有约束

- 限流为固定窗口实现，非滑动窗口或令牌桶。
- Consumer 为逐条消费落库，未做批量写入优化。
- Consumer 已支持基于 event_id 的幂等写入检查。
- 单条消息处理失败时写入本地 dead letter JSONL 文件，Consumer 不退出。
- 缓存存在 TTL 内短暂延迟。
- P95 统计为本地验证实现，通过查询所有 `duration_ms` 后在 Python 内存中计算；大数据量场景下建议改用数据库窗口函数、统计表或离线预聚合。
- 本项目不宣称支持百万级并发。
- 本项目不替代 ELK、Loki、Prometheus、Grafana 等生产级可观测平台。

### 后续优化方向

- Consumer 批量消费与批量写入 MySQL，降低单条写入开销。
- Kafka Consumer Lag 监控，观察消息堆积情况。
- 将实时统计改为统计表预聚合，减少每次查询扫描明细表。
- P95 计算改为数据库侧窗口函数、近似分位数或离线预聚合。
- Redis 限流算法从固定窗口扩展为滑动窗口或令牌桶。
- Dead letter 从本地 JSONL 文件扩展为 Kafka DLQ Topic，并增加重试机制。
- 对高频查询字段增加合适索引，但需要权衡索引对写入性能的影响。