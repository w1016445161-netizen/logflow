# LogFlow Day 6 — Locust 压测报告

> 所有性能数据均为"待填写"。请在实际运行压测后填入结果。

---

## 1. 压测环境

| 项目 | 值 |
|---|---|
| 操作系统 | Windows + Docker Desktop |
| FastAPI | localhost:8000 |
| MySQL | Docker, localhost:3307 |
| Redis | Docker, localhost:6379 |
| Kafka | Docker, localhost:9092 |
| 写入模式 | 待填写（sync / kafka） |
| Consumer 状态 | 待填写（已启动 / 未启动） |
| 本机 CPU / 内存 | 待填写 |
| Python 版本 | 待填写 |
| 测试日期 | 待填写 |

---

## 2. 压测目标

- 验证 POST /api/events 高频日志上报能力。
- 对比 sync 与 kafka 写入模式下的接口响应差异。
- 验证 Redis 限流对异常 client_id 的保护效果。
- 记录真实 RPS/QPS、平均响应时间、P95 响应时间和错误率。
- 观察是否出现 429、Kafka fallback 或 Consumer 消费滞后。

---

## 3. 压测命令

```powershell
cd D:\projects\logflow\backend

# 主链路压测
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_100.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_300.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_locust_500.ps1

# 限流专项
powershell -ExecutionPolicy Bypass -File .\scripts\perf\run_rate_limit_check.ps1
```

---

## 4. 结果记录表

> 所有数值均为"待填写"，实际运行后填入。

| 模式 | 并发数 | Spawn Rate | 时长 | RPS/QPS | 平均响应时间(ms) | P95(ms) | 错误率 | 备注 |
|---|---:|---:|---:|---:|---:|---:|---|
| sync | 100 | 10/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | |
| sync | 300 | 30/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | |
| sync | 500 | 50/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | |
| kafka | 100 | 10/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | Consumer 已启动 |
| kafka | 300 | 30/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | Consumer 已启动 |
| kafka | 500 | 50/s | 2m | 待填写 | 待填写 | 待填写 | 待填写 | Consumer 已启动 |

---

## 5. Redis 限流专项结果

| 测试项 | 并发数 | 时长 | 是否出现 429 | 非预期错误率 | 备注 |
|---|---:|---:|---|---|
| 固定 client_id 限流测试 | 50 | 1m | 待填写 | 待填写 | 429 为预期行为 |

---

## 6. 瓶颈分析

- **sync 模式可能瓶颈**：MySQL 同步写入、数据库连接数、ORM 写入成本。
- **kafka 模式可能瓶颈**：Kafka producer ack、Consumer 消费速度、MySQL 落库速度。
- **Redis 限流表现**：待填写。
- **错误率说明**：待填写。
- **是否出现 429**：待填写。
- **是否出现 Kafka fallback**：待填写。
- **Consumer 是否出现明显堆积**：待填写。
- **本机资源占用观察**：待填写。

---

## 7. CSV 输出位置

- `docs/performance/locust_100_stats.csv`
- `docs/performance/locust_300_stats.csv`
- `docs/performance/locust_500_stats.csv`
- `docs/performance/rate_limit_check_stats.csv`

---

## 8. 截图位置

截图由用户手动保存：

- `docs/images/locust_100.png`
- `docs/images/locust_300.png`
- `docs/images/locust_500.png`
- `docs/images/rate_limit_check.png`

---

> 本报告模板不含任何编造数据，所有结果由实际运行后填写。
