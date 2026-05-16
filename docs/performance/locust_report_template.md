# LogFlow — Locust 压测报告

本报告记录 LogFlow 在本机 Windows + Docker Desktop 环境下的 Locust 压测结果，用于验证 API 网关访问日志采集链路在不同写入模式下的表现。

本次压测分为三类：

- **Mixed workload**：同时压测日志上报接口和统计查询接口，用于观察写入与查询并存时的系统表现。
- **Ingest-only**：只压测 `POST /api/events`，用于观察日志上报主链路性能。
- **Rate-limit check**：使用固定 `client_id` 高频请求，用于验证 Redis 固定窗口限流能力。

> 本报告中的数据均来自本机实际运行结果。不同机器、Docker Desktop 配置、后台进程和数据库状态都会影响结果，因此数据仅作为本项目本地压测参考。

---

## 1. 压测环境

| 项目 | 值 |
|---|---|
| 操作系统 | Windows + Docker Desktop |
| FastAPI | localhost:8000 |
| MySQL | Docker, localhost:3307 |
| Redis | Docker, localhost:6379 |
| Kafka | Docker, localhost:9092 |
| Python 版本 | 待填写 |
| 本机 CPU / 内存 | 待填写 |
| 测试日期 | 2026-05-16 |
| 测试工具 | Locust |
| 测试说明 | 本地单机压测，非生产环境基准测试 |

---

## 2. 压测目标

本次压测主要验证以下问题：

1. `POST /api/events` 在高频日志上报场景下的吞吐与延迟表现。
2. `sync` 与 `kafka` 两种写入模式在接口响应时间上的差异。
3. Kafka 异步写入是否能够降低日志上报接口对 MySQL 同步写入的依赖。
4. 混合负载下，统计查询接口是否会与写入链路产生资源竞争。
5. Redis 固定窗口限流是否能保护异常高频 `client_id` 请求。
6. 是否出现 429、Kafka fallback、Consumer 明显堆积或接口错误。

---

## 3. 压测命令

```powershell
cd D:\projects\logflow\backend

# mixed workload：日志上报 + 统计查询
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_100.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_300.ps1

# ingest-only：只压测 POST /api/events
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_ingest_300.ps1

# Redis 限流专项
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_rate_limit_check.ps1
```

Kafka 模式压测前需要先将 `.env` 中的写入模式切换为：

```env
EVENT_WRITE_MODE=kafka
```

然后重启 FastAPI，并启动 Consumer：

```powershell
cd D:\projects\logflow\backend
.\.venv\Scripts\python.exe -m app.kafka.consumer
```

压测结束后建议将 `.env` 改回：

```env
EVENT_WRITE_MODE=sync
```

---

## 4. Mixed workload 压测结果

Mixed workload 同时压测：

- `POST /api/events`
- `GET /api/stats/overview`
- `GET /api/stats/top-paths`

该场景用于观察日志写入和实时统计查询同时存在时的系统表现。

| 模式 | 并发数 | Spawn Rate | 时长 | RPS/QPS | 平均响应时间(ms) | P95(ms) | 错误率 | 备注 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sync | 100 | 10/s | 2m | 307.32 | 279.78 | 420 | 0.00% | MySQL 同步写入，存在少量长尾请求，最大响应时间约 10.29s |
| sync | 300 | 30/s | 2m | 195.20 | 1435.46 | 1700 | 0.00% | 并发升高后吞吐下降，平均响应时间和 P95 明显升高，最大响应时间约 21.24s |
| kafka | 100 | 10/s | 2m | 368.12 | 219.91 | 260 | 0.00% | Consumer 已启动；相比 sync 100，RPS 提升，平均响应时间和 P95 降低；存在极少数长尾请求，最大响应时间约 41.99s |
| kafka | 300 | 30/s | 2m | 227.65 | 1234.08 | 3100 | 0.07% | POST /api/events 0 失败，失败集中在 /api/stats/overview，说明实时统计查询是当前瓶颈 |

### 4.1 Mixed workload 结果分析

在 `sync` 模式下，`POST /api/events` 会在请求链路中同步写入 MySQL。100 并发时系统能够保持 0.00% 错误率，P95 为 420ms；当并发提升到 300 后，错误率仍为 0.00%，但 RPS 从 307.32 下降到 195.20，平均响应时间从 279.78ms 上升到 1435.46ms，P95 上升到 1700ms。

这说明同步写库模式在更高并发下会受到 MySQL 写入、SQLAlchemy ORM、数据库连接和本机 Docker Desktop 资源限制影响，出现明显延迟上升。

在 `kafka` 模式下，100 并发表现优于 sync 模式，RPS 从 307.32 提升到 368.12，平均响应时间从 279.78ms 降至 219.91ms，P95 从 420ms 降至 260ms。

在 300 并发 mixed workload 中，kafka 模式整体错误率约为 0.07%。从 failures.csv 看，失败全部集中在 `GET /api/stats/overview`，`POST /api/events` 未出现失败。这说明日志上报链路本身保持可用，但实时统计查询在高并发写入期间成为瓶颈。

---

## 5. Kafka 300 mixed workload 接口拆分结果

为了进一步定位 kafka 300 mixed workload 的失败来源，对 `locust_300_stats.csv` 中各接口数据进行拆分：

| 接口 | 请求数 | 失败数 | 平均响应时间(ms) | P95(ms) | RPS |
|---|---:|---:|---:|---:|---:|
| POST /api/events | 22669 | 0 | 1145.61 | 2900 | 189.36 |
| GET /api/stats/overview | 2302 | 20 | 2043.90 | 12000 | 19.23 |
| GET /api/stats/top-paths | 2282 | 0 | 1295.95 | 9400 | 19.06 |
| Aggregated | 27253 | 20 | 1234.08 | 3100 | 227.65 |

### 5.1 接口拆分结果分析

Kafka 300 mixed workload 中，`POST /api/events` 共处理 22669 次请求，失败数为 0，说明 Kafka 日志上报链路在本次测试中保持可用。

失败全部集中在 `GET /api/stats/overview`，该接口出现 20 次失败，P95 达到 12000ms。原因可能是高并发写入期间，统计接口需要进行总量、错误率、平均耗时、P95、热门路径等实时聚合查询，与写入链路竞争 MySQL 资源。

当前 P95 统计为本地验证实现，会查询 `duration_ms` 后在 Python 内存中排序计算。随着数据量增加，该方式会带来查询和内存开销。后续应考虑将统计计算改为数据库窗口函数、统计表预聚合或异步指标计算。

---

## 6. Ingest-only 压测结果

Ingest-only 只压测：

- `POST /api/events`

该场景不包含统计查询接口，用于单独观察日志上报主链路性能，排除统计接口干扰。

| 模式 | 并发数 | Spawn Rate | 时长 | RPS/QPS | 平均响应时间(ms) | P95(ms) | 错误率 | 备注 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sync | 300 | 30/s | 2m | 313.02 | 894.03 | 1100 | 0.00% | 只压测 POST /api/events，同步写入 MySQL |
| kafka | 300 | 30/s | 2m | 603.45 | 455.01 | 550 | 0.00% | 只压测 POST /api/events，Consumer 已启动 |
| sync | 500 | 50/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | 可选，本机资源不足时可不填写 |
| kafka | 500 | 50/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | 可选，本机资源不足时可不填写 |

### 6.1 Ingest-only 结果分析

Ingest-only 压测只压测 `POST /api/events`，不包含统计查询接口，因此更能反映日志上报主链路的性能表现。

300 并发下，sync 模式需要在请求链路中同步写入 MySQL，RPS 为 313.02，平均响应时间为 894.03ms，P95 为 1100ms。切换到 kafka 模式后，接口只负责将事件写入 Kafka，MySQL 落库由 Consumer 异步完成，RPS 提升到 603.45，平均响应时间下降到 455.01ms，P95 下降到 550ms，错误率仍为 0.00%。

该结果说明，在纯日志上报场景下，Kafka 异步写入能够有效降低接口对 MySQL 同步写入的依赖，提升吞吐并降低延迟。

### 6.2 Ingest-only 优化幅度

| 指标 | sync 300 | kafka 300 | 变化 |
|---|---:|---:|---:|
| RPS/QPS | 313.02 | 603.45 | 提升约 92.8% |
| 平均响应时间(ms) | 894.03 | 455.01 | 降低约 49.1% |
| P95(ms) | 1100 | 550 | 降低约 50.0% |
| 错误率 | 0.00% | 0.00% | 保持 0.00% |

---

## 7. Redis 限流专项结果

Redis 限流专项测试使用固定 `client_id` 高频请求，用于验证固定窗口限流能力。

| 测试项 | 并发数 | 时长 | 是否出现 429 | 非预期错误率 | 平均响应时间(ms) | P95(ms) | 备注 |
|---|---:|---:|---|---:|---:|---:|---|
| 固定 client_id 限流测试 | 50 | 1m | 是 | 0.00% | 62.97 | 82 | 429 为预期行为 |

### 7.1 Redis 限流专项结果分析

Redis 限流专项测试使用固定 `client_id` 进行高频请求。由于系统默认限制同一 `client_id` 在固定窗口内的请求次数，超过阈值后会返回 429。该压测脚本将 429 视为预期行为，因此 Failure Count 为 0 表示没有出现非预期错误，而不是没有触发限流。

本次测试共发送 34146 次请求，平均响应时间 62.97ms，P95 为 82ms，非预期错误率为 0.00%。结果说明 Redis 固定窗口限流链路可以稳定处理异常高频 `client_id` 请求，并避免这类请求继续冲击后续写入链路。

---

## 8. 瓶颈分析

### 8.1 sync 模式瓶颈

sync 模式下，日志上报接口会在请求链路中同步写入 MySQL。随着并发升高，请求响应时间明显上升，主要瓶颈可能来自：

- MySQL 同步写入。
- SQLAlchemy ORM 单条插入开销。
- 数据库连接池竞争。
- 本机 Docker Desktop 资源限制。
- 写入和统计查询同时存在时的资源竞争。

### 8.2 kafka 模式瓶颈

kafka 模式将接口写入和 MySQL 落库解耦，能够降低日志上报接口对数据库同步写入的依赖。但在高并发下仍可能受到以下因素影响：

- Kafka Producer ack 等待。
- Kafka broker 本机容器资源限制。
- Consumer 消费和 MySQL 落库速度。
- FastAPI 本机处理能力。
- 结构化日志输出开销。

### 8.3 统计查询瓶颈

mixed workload 的 kafka 300 测试显示，失败集中在 `GET /api/stats/overview`。该接口需要进行实时聚合，包括总量、错误率、平均耗时、P95、热门路径等指标。

当前 P95 统计通过查询 `duration_ms` 后在 Python 内存中排序计算，适合本地验证，但不适合大数据量场景。后续应考虑：

- 使用数据库窗口函数或近似分位数算法。
- 引入统计表进行预聚合。
- 在 Consumer 消费时异步维护统计结果。
- 将明细日志分析迁移到更适合分析型查询的存储中。

---

## 9. 后续优化方向

- Consumer 批量消费与批量写入 MySQL，降低单条写入开销。
- Kafka Consumer Lag 监控，观察消息堆积情况。
- 将实时统计改为统计表预聚合，减少每次查询扫描明细表。
- P95 计算改为数据库侧窗口函数、近似分位数或离线预聚合。
- Redis 限流算法从固定窗口扩展为滑动窗口或令牌桶。
- Dead letter 从本地 JSONL 文件扩展为 Kafka DLQ Topic，并增加重试机制。
- 对高频查询字段增加合适索引，但需要权衡索引对写入性能的影响。

---

## 10. CSV 输出位置

本地原始 CSV 数据位于：

```text
docs/performance/
```

主要文件包括：

```text
sync_100_stats.csv
sync_300_stats.csv
kafka_100_stats.csv
kafka_300_mixed_stats.csv
sync_ingest_300_stats.csv
kafka_ingest_300_stats.csv
rate_limit_check_stats.csv
```

> 公开仓库可只提交本 Markdown 报告，不提交 CSV 原始数据，避免仓库文件过多。

---

## 11. 截图位置

如需在 README 或答辩材料中展示截图，可手动保存到：

```text
docs/images/
```

建议截图文件名：

```text
locust_mixed_100.png
locust_mixed_300.png
locust_ingest_300.png
rate_limit_check.png
```

---

## 12. 总结

本次压测分为 mixed workload、ingest-only 和 Redis 限流专项三类。

Mixed workload 用于观察日志写入和统计查询同时存在时的系统表现。结果显示，在高并发写入期间，实时统计接口 `GET /api/stats/overview` 会成为主要瓶颈，失败集中在统计查询而非日志上报接口。

Ingest-only 用于单独观察日志上报主链路性能。300 并发下，kafka 模式相比 sync 模式将 RPS 从 313.02 提升到 603.45，平均响应时间从 894.03ms 降至 455.01ms，P95 从 1100ms 降至 550ms，错误率均为 0.00%。该结果验证了 Kafka 异步削峰对日志上报主链路的优化效果。

Redis 限流专项测试验证了固定窗口限流能力。固定 `client_id` 高频请求会触发 429，且无非预期错误，说明限流逻辑可以保护异常客户端，避免单一 `client_id` 持续冲击写入链路。

综上，LogFlow 在本机压测环境下验证了日志上报、限流、Kafka 异步写入和统计查询链路的基本可用性，同时也暴露了实时统计查询在高并发写入期间的瓶颈。后续优化重点应放在统计预聚合、Consumer 批量落库、Kafka 消费堆积监控和 dead letter 重试机制上。