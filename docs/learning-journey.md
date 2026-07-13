# 电商数仓 — 5 周学习旅程

> 从 0 基础到端到端数仓 + Airflow 自动化  
> 100 万订单 · 320 万行 · 4 层数仓 · 6 道面试 SQL · 17 个工程坑

---

## 项目概览

**目标**：独立设计并实现完整电商数仓，用于数据岗求职作品集。

**技术栈**：Python 3.13 + MySQL 8.0 + Apache Airflow 2.10 + Docker Desktop + Git

**最终规模**：

| 表 | 行数 |
|---|---|
| ods_users | 100,000 |
| ods_products | 5,000 |
| ods_orders | 1,000,000 |
| ods_order_items | 2,099,785 |
| dws_user_summary | 100,000 |
| dws_product_summary | 5,000 |
| dws_date_summary | 367 |
| **总计** | **3,310,152** |

---

## Week 1：数据生成

### 产出

- 100 万订单 + 10 万用户 + 5 千商品 + 210 万订单明细
- 用 `Faker('zh_CN')` 生成中文名、城市、手机号
- 用 `random.choices(weights=...)` 控制业务分布

### 数据特征

```
订单状态分布：
  paid      649,339 (64.93%)
  shipped   150,231 (15.02%)
  received  100,469 (10.05%)
  cancelled  50,100 ( 5.01%)
  refunded   49,861 ( 4.99%)
客单价：897.96 元
时间跨度：2025-06-15 ~ 2026-06-16（366 天）
```

### 核心教训：数据生成要符合业务约束 ⭐

第一版 `generate_orders.py` 用 `random.randint` 选商品，同一订单可能选到重复商品 → `IntegrityError: Duplicate entry`。修复：改用 `random.sample` 不重复选取。**主键约束是发现数据 bug 的最好工具。**

---

## Week 2：ODS 层

### 产出

- 4 张表入 MySQL 8.0（InnoDB + utf8mb4 + 业务主键）
- `load_to_mysql.py`：SQLAlchemy + pymysql 数据接入
- 数据验证 + DBeaver 可视化

### 7 个真实 Debug ⭐

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| 1 | C 盘爆满 | 项目/venv/数据散落 C 盘 | 统一迁到 F 盘 |
| 2 | tar.gz 解压散架 | Windows tar 行为不一致 | PowerShell `Move-Item` 整理 |
| 3 | pandas 装不上 | Python 3.6 太老 | 用 3.13 重建 venv |
| 4 | `git push` 失败 | GitHub 需代理，Git 不会自动用浏览器代理 | `git config http.proxy` |
| 5 | venv 缺依赖 | 重建 venv 后漏装 | `pip install -r requirements.txt` |
| 6 | `too many parameters` | SQLAlchemy 2.0 `to_sql(method="multi")` 超 MySQL 限制 | 换 pymysql `executemany` |
| 7 | 订单明细主键冲突 | `random.randint` 可能选重复商品 | 改用 `random.sample` |

**核心心得**：遇到工具链兼容性问题，不要死磕，换更底层的工具（pymysql 替代 SQLAlchemy）。

---

## Week 3：DWD 层

### 产出

- `dwd_orders`（100 万行）+ `dwd_order_items`（210 万行）
- **维度退化**：username/city/product_name 直接存事实表，查询不用 JOIN
- **业务标记**：`is_valid_order`（有效订单）、`is_first_order`（首单）

### 6 道面试 SQL

| # | 题目 | 关键技巧 | 结果 |
|---|------|---------|------|
| 1 | 每日新用户数 | `is_first_order = 1` 业务标记 | — |
| 2 | **7 日留存率** ⭐⭐⭐ | CTE + `DATEDIFF BETWEEN 1 AND 7` | **15.5%**（行业 10-20%） |
| 3 | 转化漏斗 | `CASE WHEN status IN (...)` 分层计数 | 下单→支付→发货→收货 |
| 4 | 复购率 | `COUNT(*) >= 2` 判断 | 99.9%（偏高，数据特征） |
| 5 | 复购周期分布 | `LAG() OVER (PARTITION BY user_id)` | 60% 在 30 天内 |
| 6 | 连续 N 天有订单 ⭐⭐ | `date - ROW_NUMBER()` 分组技巧 | — |

### 核心概念

- **维度退化**：避免分析查询频繁 JOIN，查询性能提升
- **窗口函数三大金刚**：`ROW_NUMBER()` / `LAG()` / `SUM() OVER`
- **业务标记 vs 原始字段**：`status` 是原始值，`is_valid_order` 是分析口径

---

## Week 4：DWS 层

### 产出

- 3 张主题宽表：`dws_user_summary`（10 万）/ `dws_product_summary`（5 千）/ `dws_date_summary`（367 天）
- **RFM 8 类客户分层**：NTILE(5) 打分 + CASE 映射

### RFM 结果

| 客户分层 | 用户数 | 占比 | 营销策略 |
|---------|--------|------|----------|
| 重要价值客户 | 13,125 | 13.1% | VIP 专属服务 |
| 重要发展客户 | 8,343 | 8.3% | 新客优惠券 |
| 重要保持客户 | 1,910 | 1.9% | 定期唤醒 |
| 重要挽留客户 | 2,563 | 2.6% | 大额优惠券 |
| 流失客户 | 61,564 | 61.6% | 不投入资源 |

### 关键 SQL 难点

`dws_date_summary` 遇到 MySQL 8.0 `only_full_group_by` strict 模式，用子查询嵌套 GROUP BY 解决。

---

## Week 5：Airflow 自动化调度

### 演进过程

**第一版**（废弃）：`docker run standalone` + PythonOperator → webserver 不稳定、无法并行

**第二版**（当前）：`docker compose` + DockerOperator + LocalExecutor

```
[ods_to_dwd] → [dwd_to_dws] → [data_quality_check] → [send_notification]
 DockerOperator   DockerOperator    DockerOperator        EmailOperator
   37 min            13 min             2 sec                3 sec
```

- 每天凌晨 2 点自动跑
- Task 失败 → 自动发邮件告警
- 全部成功 → EmailOperator 发 HTML 完成通知

### 工程坑

| 坑 | 严重程度 |
|----|---------|
| MySQL 元数据锁死锁（`docker rm -f` 残留连接） | ⚠️ 最致命 |
| `auto_remove="success"` → Docker API 409 | 高 |
| Web UI 日志 403（secret_key 不一致） | 中 |
| 并发 TRUNCATE 冲突（缺 `max_active_runs=1`） | 高 |
| Docker bridge 网络下 INSERT 慢（37 分钟） | 中 |

详细记录：[07-airflow-dag/airflow-practice-log.md](../07-airflow-dag/airflow-practice-log.md)

---

## 关键收获

### 工程思维

1. **先看完整报错，再动手** — 反复重试不如仔细读一次错误信息
2. **工具链兼容性是真实工程的坑** — 新版本可能引入意外问题，必要时换底层工具
3. **数据完整性靠约束保证** — 主键/外键/唯一索引是护城河
4. **跨平台是大坑** — Windows ≠ Linux ≠ 容器，路径/权限/字符集都可能不同
5. **容器是临时工，镜像才是真相** — 不在运行时改容器，改 Dockerfile

### 数仓设计

6. **维度退化** — 把常用维度字段存进事实表，避免分析查询频繁 JOIN
7. **业务标记统一口径** — `is_valid_order` 比每次写 `status IN (...)` 更清晰
8. **窗口函数解决 80% 分析需求** — ROW_NUMBER / LAG / NTILE 是面试必修

---

## 简历项目描述

> **端到端电商数仓 + Airflow 自动化 ETL 编排** | [GitHub](https://github.com/Three-rgb/ecommerce-data-warehouse)
>
> 独立设计并实现完整电商数仓（5 周）：
> - **4 层数仓架构**（ODS / DWD / DWS / ADS），处理 100 万订单 320 万明细，全部入 MySQL 8.0
> - **6 道面试 SQL**：7 日留存率 15.5%、转化漏斗、复购周期、连续登录等
> - **RFM 8 类客户分层**：NTILE 评分 + CASE 映射，识别 13,125 个重要价值客户
> - **Airflow 2.10 DockerOperator + LocalExecutor**：4 任务 DAG 每天凌晨 2 点自动跑，QQ 邮箱告警
> - **解决 17 个真实工程问题**：MySQL 元数据锁、Docker API 冲突、跨平台路径、SQL strict 模式等
>
> **技术栈**：Python 3.13 · MySQL 8.0 · Apache Airflow 2.10 · Docker Desktop · Git

---

**记录时间**：2026-06 ~ 2026-07  
**作者**：zhao  
**项目状态**：5 周全部完成 ✅
