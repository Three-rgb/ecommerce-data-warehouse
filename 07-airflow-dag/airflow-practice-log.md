# Airflow 自动化调度 — 实战复盘

> **日期**：2026-07-13  
> **耗时**：约 4 小时（含 10+ 次排障）  
> **结果**：4 任务 DAG 全绿，邮件告警配置完成，50 分钟跑完 320 万行 ETL

---

## 架构演进

### 方案 1：Standalone 模式（被淘汰）

```
docker run ... apache/airflow:2.10.2 standalone
  └── 单进程跑 webserver + scheduler
       └── PythonOperator 进程内 importlib 调 ETL 脚本
```

**问题**：webserver 不稳定（已知 bug）、无法并行、Task 共享进程空间。

### 方案 2：DockerOperator + LocalExecutor（最终采用）

```
docker compose up
  ├── postgres          — Airflow 元数据库
  ├── airflow-webserver — Web UI (:8080)
  ├── airflow-scheduler — LocalExecutor + DockerOperator
  │    └── /var/run/docker.sock 挂载 → 启临时容器
  └── 临时 ETL 容器      — ecommerce-etl:latest
       ├── ods_to_dwd      (37 min)
       ├── dwd_to_dws      (13 min)
       ├── quality_check   (2 sec)
       └── send_notification (3 sec, EmailOperator)
```

**优势**：Task 隔离（独立容器）、LocalExecutor 并行、webserver 稳定、镜像即合约。

---

## 踩坑清单

### 坑 1：MySQL 元数据锁死锁 ⚠️ 最致命

**现象**：`ods_to_dwd` 卡 47 分钟，`SHOW PROCESSLIST` 显示 `DROP TABLE ... Waiting for table metadata lock`。

**根因**：Docker 容器被 `docker rm -f` 杀掉时，Python 进程死掉但 MySQL 事务未回滚，`dwd_order_items` 上的元数据锁未释放。后续每次 ETL 跑 `DROP TABLE` 都永久等待。

**解决**：重启 MySQL 服务（`Restart-Service MySQL`），所有锁释放。

**教训**：
- DockerOperator 容器被强行杀掉 → MySQL 连接残留 → 元数据锁泄漏
- 不要用 `docker rm -f` 杀正在连数据库的容器
- 定期检查 `SHOW PROCESSLIST`，发现长时间 `Waiting for table metadata lock` 立刻处理

---

### 坑 2：`auto_remove="success"` 导致 Docker API 409 冲突

**现象**：Task 报错 `409 Client Error: cannot remove container - container is running`，重试不停的建新容器、旧容器堆积、最终超时。

**根因**：`auto_remove="success"` 告诉 Docker daemon 自动删容器，但 DockerOperator 代码里也会调 `remove_container()`。容器还在运行时 Airflow 去删 → 409。

**解决**：`auto_remove=False`，让 Airflow 全权管理容器生命周期。

```python
# 之前（有问题）
DockerOperator(task_id="...", auto_remove="success", ...)

# 修复后
DockerOperator(task_id="...", auto_remove=False, ...)
```

---

### 坑 3：Web UI 查看日志 403 错误

**现象**：Airflow Web UI 点 "View Logs" 报 `403 FORBIDDEN`，无法看到任务实时输出。

**根因**：webserver 和 scheduler 的 `secret_key` 不一致。Web UI 向 scheduler 的日志服务（`:8793`）请求日志时签名验证失败。

**解决**：在 `docker-compose.airflow.yml` 中统一设置：

```yaml
AIRFLOW__WEBSERVER__SECRET_KEY: ecommerce_dw_airflow_secret_2026
```

所有 Airflow 服务共享同一个密钥。

---

### 坑 4：`max_active_runs` 缺失导致并发冲突

**现象**：手动触发多次 DAG，多个 `ods_to_dwd` 同时跑，都在 `TRUNCATE + INSERT` 同一张表，互相锁死。

**根因**：DAG 没有设置 `max_active_runs`，LocalExecutor 允许同一 DAG 的多个 Run 并行。

**解决**：

```python
with DAG(
    dag_id="ecommerce_etl_docker",
    max_active_runs=1,  # TRUNCATE + INSERT 不能并行
    ...
)
```

---

### 坑 5：Docker 网络下 MySQL INSERT 速度慢

**现象**：`ods_to_dwd` 的 `INSERT INTO dwd_order_items ... SELECT ... JOIN` 跑了 37 分钟（2.1M 行）。

**根因**：Docker bridge 网络下 `host.docker.internal` 解析有额外开销。MySQL 的 `INSERT...SELECT` 是单事务原子操作，2.1M 行全部插入后才 COMMIT，期间 `COUNT(*)` 显示 0。

**现状**：全管道 50 分钟，对每天凌晨 2 点自动跑的 ETL 来说可接受。

**优化方向**（未实施）：
- 分批 COMMIT（每 10 万行提交一次）
- 用 `network_mode: host`（仅 Linux，Windows Docker Desktop 不支持）
- 优化 MySQL InnoDB buffer pool

---

### 坑 6：Git Bash 路径自动转换

**现象**：`docker run ecommerce-etl python /app/send_notification.py` 报 `can't open file 'F:/Git/app/send_notification.py'`。

**根因**：Git Bash（MSYS2）把以 `/` 开头的路径自动转成 Windows 绝对路径。`/app/` 被转成 `F:/Git/app/`。

**解决**：命令前加 `MSYS_NO_PATHCONV=1`：

```bash
MSYS_NO_PATHCONV=1 docker run --rm ecommerce-etl:latest python /app/send_notification.py
```

---

### 坑 7：docker-compose YAML 多行命令解析异常

**现象**：`airflow-init` 容器报 `/bin/bash: line 4: --username: command not found`。

**根因**：YAML `>` 折叠多行时，bash 的 `&&` 续行被破坏，`airflow users create` 的参数被当成独立命令执行。

**解决**：改用 JSON 数组格式：

```yaml
# 之前（有问题）
command: >
  bash -c "airflow db migrate && airflow users create ..."

# 修复后
command: ["bash", "-c", "airflow db migrate && airflow users create --username admin ..."]
```

---

## SMTP 邮件告警配置

使用 QQ 邮箱 SMTP，配置在 `docker-compose.airflow.yml`：

```yaml
AIRFLOW__SMTP__SMTP_HOST: smtp.qq.com
AIRFLOW__SMTP__SMTP_STARTTLS: 'true'
AIRFLOW__SMTP__SMTP_PORT: '587'
AIRFLOW__SMTP__SMTP_USER: 3075758453@qq.com
```

DAG 中两类邮件：

| 场景 | 触发方式 | 配置 |
|------|---------|------|
| **Task 失败** | 自动 | `email_on_failure=True` |
| **Task 重试** | 自动 | `email_on_retry=True` |
| **管道成功** | EmailOperator | DAG 最后一个 Task |

QQ 邮箱授权码获取：QQ 邮箱 → 设置 → 账户 → POP3/SMTP 服务 → 生成授权码。

---

## 项目文件结构

```
├── docker-compose.airflow.yml    # Airflow 集群（postgres + webserver + scheduler）
├── docker/
│   ├── airflow/Dockerfile        # Airflow 镜像（预装 docker provider）
│   └── etl/
│       ├── Dockerfile            # ETL 任务镜像（pymysql + pandas + 所有脚本）
│       └── entrypoint.sh         # 入口：有参数执行 Task / 无参数显示帮助
├── .env.airflow                  # 环境变量（SMTP_PASSWORD）
├── 07-airflow-dag/
│   ├── dags/
│   │   ├── ecommerce_etl_docker.py  # DockerOperator 版 DAG
│   │   ├── ecommerce_etl.py         # 旧版 PythonOperator DAG（保留）
│   │   └── hello_world.py
│   ├── plugins/
│   │   └── etl_functions.py         # 旧版 ETL 函数库（保留）
│   └── scripts/
│       ├── quality_check.py         # DockerOperator 独立脚本
│       └── send_notification.py     # DockerOperator 独立脚本
```

---

## 常用命令

```bash
# === 构建 ===
docker build -f docker/etl/Dockerfile -t ecommerce-etl:latest .

# === 启动/停止 ===
docker compose -f docker-compose.airflow.yml --env-file .env.airflow up -d
docker compose -f docker-compose.airflow.yml --env-file .env.airflow down

# === Web UI ===
# http://localhost:8080  admin / admin

# === CLI ===
docker exec airflow-scheduler airflow dags list                        # 查看所有 DAG
docker exec airflow-scheduler airflow dags trigger ecommerce_etl_docker # 手动触发
docker exec airflow-scheduler airflow tasks list ecommerce_etl_docker   # 查看 Task
```

---

## 最终验证数据

| 表 | 行数 | 预期 |
|---|---|---|
| dwd_orders | 1,000,000 | 100 万 ✅ |
| dwd_order_items | 2,099,785 | 210 万 ✅ |
| dws_user_summary | 100,000 | 10 万 ✅ |
| dws_product_summary | 5,000 | 5 千 ✅ |
| dws_date_summary | 367 | ~366 ✅ |

**DAG 运行记录**：

```
run_id: manual__2026-07-13T12:19:59+00:00
  ods_to_dwd         ✅ 37 min  (12:20 → 12:56)
  dwd_to_dws         ✅ 13 min  (12:56 → 13:09)
  data_quality_check ✅  2 sec  (13:09)
  send_notification  ✅  3 sec  (13:09)
```
