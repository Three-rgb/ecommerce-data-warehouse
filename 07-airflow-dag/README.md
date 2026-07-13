# Week 5 — Airflow 调度编排

> **实战复盘**：[airflow-practice-log.md](./airflow-practice-log.md) — 7 个真实工程坑 + 完整踩坑记录

## 什么是 Airflow？

Apache Airflow 是 Airbnb 开源的**工作流调度平台**，核心能力：
- 把多个任务编排成 DAG（有向无环图）
- 按时间/依赖自动执行
- 监控任务状态（成功/失败/重试）
- 失败告警（邮件/钉钉/Slack）

## 核心概念

### DAG（有向无环图）

```
[ods_to_dwd] → [dwd_to_dws] → [data_quality_check] → [send_notification]
     ↓ 失败
[email_on_failure 自动告警]
```

### Operator（任务类型）

| Operator | 用途 | 本项目使用 |
|----------|------|-----------|
| `DockerOperator` | 启临时容器跑任务 | ✅ ods_to_dwd / dwd_to_dws / quality_check |
| `EmailOperator` | 发邮件 | ✅ send_notification |
| `PythonOperator` | 跑 Python 函数 | 旧版 ecommerce_etl.py |
| `BashOperator` | 跑 shell 命令 | hello_world.py |

### Executor（执行器）

| Executor | 适用场景 | 本项目 |
|----------|---------|--------|
| `LocalExecutor` | 单机并行 | ✅ 当前方案 |
| `SequentialExecutor` | 开发/测试 | Standalone 模式内置 |
| `CeleryExecutor` | 多机分布式 | 生产集群 |

### Schedule（调度规则）

- `schedule_interval='0 2 * * *'` — 每天凌晨 2 点
- `schedule_interval='@daily'` — 每天
- `schedule_interval=None` — 仅手动触发

## 部署架构

```
docker compose up
  ├── postgres          — Airflow 元数据库
  ├── airflow-webserver — Web UI (:8080)
  ├── airflow-scheduler — LocalExecutor
  │    ├── 挂载 /var/run/docker.sock（启临时容器）
  │    └── 挂载 ./dags/（DAG 文件热加载）
  │
  └── DockerOperator 临时容器
       └── ecommerce-etl:latest
            ├── python /app/load_to_dwd.py
            ├── python /app/load_to_dws.py
            └── python /app/quality_check.py
```

**启动**：

```bash
# 首次：构建 ETL 镜像
docker build -f docker/etl/Dockerfile -t ecommerce-etl:latest .

# 启动集群
docker compose -f docker-compose.airflow.yml --env-file .env.airflow up -d

# Web UI
# http://localhost:8080  admin / admin
```

详细配置见项目根目录的 `docker-compose.airflow.yml`。

## 文件结构

```
07-airflow-dag/
├── README.md                      # 本文档
├── airflow-practice-log.md        # 实战踩坑复盘（7 个坑）
├── dags/
│   ├── ecommerce_etl_docker.py    # ✅ DockerOperator + EmailOperator 版 DAG
│   └── hello_world.py             #    入门 DAG
├── scripts/
│   └── quality_check.py           #    DockerOperator 独立脚本
└── logs/                          #    Airflow 日志目录
```

## DAG 详情

### ecommerce_etl_docker（生产 DAG）

```
[ods_to_dwd] ──→ [dwd_to_dws] ──→ [data_quality_check] ──→ [send_notification]
 DockerOperator   DockerOperator      DockerOperator           EmailOperator
  37 min            13 min              2 sec                   3 sec
```

| 配置项 | 值 |
|--------|-----|
| schedule | 每天凌晨 2 点 (`0 2 * * *`) |
| max_active_runs | 1（防止 TRUNCATE + INSERT 并行冲突） |
| retries | 1 次，间隔 5 分钟 |
| email_on_failure | ✅ 自动发告警邮件 |
| email_on_retry | ✅ 重试也通知 |
| SMTP | QQ 邮箱 (smtp.qq.com:587) |

### hello_world（入门 DAG）

3 个任务串行：`PythonOperator → BashOperator → PythonOperator`，验证 Airflow 基础功能。

## 邮件告警

**三类邮件**：

| 场景 | 触发方式 | 配置位置 |
|------|---------|---------|
| Task 失败 | Airflow 自动 | `default_args.email_on_failure=True` |
| Task 重试 | Airflow 自动 | `default_args.email_on_retry=True` |
| 管道成功 | EmailOperator | DAG 最后一个 Task |

**SMTP 配置**在 `docker-compose.airflow.yml` 环境变量中。QQ 邮箱需要授权码（非登录密码）。

## 为什么用 DockerOperator 而不是 PythonOperator？

| 维度 | PythonOperator | DockerOperator |
|------|---------------|----------------|
| 任务隔离 | ❌ 共享进程空间 | ✅ 独立容器 |
| 依赖管理 | 进容器 pip install | Dockerfile 预装 |
| 可复现性 | 依赖挂载路径 | 镜像即合约 |
| 面试价值 | 基础 | "生产级" |

## 学习路径

1. **理解概念**：DAG / Operator / Executor / Schedule
2. **跑 hello_world.py**：看 DAG 在 Web UI 长啥样
3. **读 ecommerce_etl_docker.py**：理解 DockerOperator 怎么用
4. **读 airflow-practice-log.md**：学 7 个真实工程坑
5. **自己触发一次**：Web UI 点 ▶ 或 CLI `airflow dags trigger`

## 真实工作场景

```
每天凌晨 2 点，Airflow 自动：
1. ODS → DWD（清洗 100 万订单）
2. DWD → DWS（聚合 3 张宽表 + RFM 客户分层）
3. 数据质量检查（行数校验）
4. 成功 → 发邮件通知数据团队
5. 失败 → 自动告警 + 5 分钟后重试
```
