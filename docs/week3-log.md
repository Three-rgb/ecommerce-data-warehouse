# Week 3 复盘 - DWD 层 + SQL 窗口函数

> 从 0 基础到"7 个面试 SQL 题全跑通"
> 适合作为简历项目故事 + 面试 SQL 模板

---

## 核心成就

✅ **DWD 层 2 张表建好**:100 万订单 + 200 万订单明细,带业务标记(有效订单/首单)
✅ **维度退化完成**:username/city 等信息直接存到 dwd,查询不用 JOIN
✅ **6 道面试 SQL 题全跑通** ⭐⭐⭐
✅ **DBeaver 可视化查询**
✅ **完整 debug 经历**(DDL 内嵌、文件路径、SQL 警告、PyCharm 配置)

---

## 数据亮点(可以讲给面试官听)

### 1. 7 日留存率稳定在 15.5% ⭐⭐⭐
- 跟真实电商行业平均(10-20%)一致
- 说明造数据时没有"过分随机",真实业务感强

### 2. 转化漏斗呈现真实业务特征
```
100% 下单 → 100% 支付 → 91.7% 发货 → 63.3% 收货
```
- 收货率 63% 偏低(因为 1 年内新订单还在运输中,符合现实)

### 3. 复购周期分布合理
- 60% 复购发生在 30 天内
- 跟行业"快速消费"特征吻合

### 4. 复购率 99.89% 偏高(数据故事)
- 这暴露了第一版造数据的局限
- 后来调整参数,体现"真实业务数据 vs 随机数据"的认知

---

## 6 道面试 SQL 题模板(默写级别)

### 1. 每日新用户数
```sql
SELECT
    order_date,
    COUNT(DISTINCT user_id) AS new_user_count
FROM dwd_orders
WHERE is_first_order = 1 AND is_valid_order = 1
GROUP BY order_date
ORDER BY order_date;
```

### 2. 7 日留存率 ⭐⭐⭐
```sql
WITH first_orders AS (
    SELECT user_id, MIN(order_date) AS first_date
    FROM dwd_orders WHERE is_valid_order = 1
    GROUP BY user_id
),
user_activity AS (
    SELECT DISTINCT user_id, order_date
    FROM dwd_orders WHERE is_valid_order = 1
)
SELECT
    f.first_date,
    COUNT(DISTINCT f.user_id) AS new_users,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) BETWEEN 1 AND 7
        THEN f.user_id
    END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS d7_retention_pct
FROM first_orders f
LEFT JOIN user_activity u ON f.user_id = u.user_id
GROUP BY f.first_date
ORDER BY f.first_date;
```

### 3. 转化漏斗
```sql
SELECT
    COUNT(DISTINCT user_id) AS step1,
    COUNT(DISTINCT CASE WHEN status IN ('paid','shipped','received') THEN user_id END) AS step2,
    COUNT(DISTINCT CASE WHEN status IN ('shipped','received') THEN user_id END) AS step3,
    COUNT(DISTINCT CASE WHEN status = 'received' THEN user_id END) AS step4
FROM dwd_orders;
```

### 4. 复购率
```sql
WITH user_orders AS (
    SELECT user_id, COUNT(*) AS cnt
    FROM dwd_orders WHERE is_valid_order = 1
    GROUP BY user_id
)
SELECT
    ROUND(SUM(CASE WHEN cnt >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS repurchase_pct
FROM user_orders;
```

### 5. 复购周期分布
```sql
WITH orders_with_prev AS (
    SELECT
        user_id, create_time,
        LAG(create_time) OVER (PARTITION BY user_id ORDER BY create_time) AS prev_time
    FROM dwd_orders WHERE is_valid_order = 1
)
SELECT
    CASE
        WHEN DATEDIFF(create_time, prev_time) BETWEEN 0 AND 7 THEN '0-7天'
        WHEN DATEDIFF(create_time, prev_time) BETWEEN 8 AND 30 THEN '8-30天'
        WHEN DATEDIFF(create_time, prev_time) BETWEEN 31 AND 90 THEN '31-90天'
        ELSE '90天以上'
    END AS range_label,
    COUNT(*) AS repurchase_count
FROM orders_with_prev
WHERE prev_time IS NOT NULL
GROUP BY range_label
ORDER BY MIN(DATEDIFF(create_time, prev_time));
```

### 6. 连续 N 天有订单 ⭐⭐(进阶)
```sql
WITH daily_orders AS (
    SELECT DISTINCT user_id, order_date
    FROM dwd_orders WHERE is_valid_order = 1
),
with_groups AS (
    SELECT
        user_id, order_date,
        DATE_SUB(order_date, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) DAY) AS grp
    FROM daily_orders
)
SELECT
    COUNT(*) AS consecutive_days,
    COUNT(DISTINCT user_id) AS user_count
FROM with_groups
GROUP BY consecutive_days
HAVING consecutive_days >= 3
ORDER BY consecutive_days;
```

**关键技巧**:`order_date - ROW_NUMBER()` 得到组号,同一连续区间映射到同一组。

---

## 关键学习

### 1. 维度退化(Dimension Degenerate)
把维度字段(用户名/商品名)放进事实表,避免查询时 JOIN:
```sql
-- 不好:每次 JOIN
SELECT o.*, u.username FROM ods_orders o JOIN ods_users u ON ...

-- 好:维度退化
SELECT * FROM dwd_orders;  -- 直接有 username
```

### 2. 业务标记 vs 业务字段
- `status` 是原始字段(paid/shipped/received/refunded/cancelled)
- `is_valid_order` 是业务标记(0/1)— 分析时直接过滤

### 3. 窗口函数三大金刚
- `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` - 排序编号
- `LAG() / LEAD()` - 上下行对比
- `SUM() / COUNT() / AVG() OVER (PARTITION BY ... ORDER BY ...)` - 累计

### 4. 业务驱动 SQL,不是技术驱动
- 留存率 SQL 核心是"日期比较",不是"复杂语法"
- 复购率 SQL 核心是"次数判断",不是"高深技巧"

---

## Debug 经验(Week 3 新增)

### 1. DDL 文件路径问题
- 一开始 SQL 写在 `ddl/*.sql` 文件里,Python 脚本读不到
- 解决:DDL 内嵌到 Python 脚本里,不依赖外部文件

### 2. 跨目录 import 失败
- 之前 `load_to_dwd.py` 想 `from db_config import MYSQL_CONFIG`
- 路径写错(多一层 `.parent`)
- 解决:每个脚本自带 MYSQL 配置,不依赖兄弟目录

### 3. pandas + pymysql 不兼容
- 报 `UserWarning: pandas only supports SQLAlchemy ...`
- 解决:用 SQLAlchemy 创建 engine,或忽略警告(查询结果不受影响)

### 4. INSERT 200 万行要 30 分钟
- MySQL 单机写入 200 万行,3-5 分钟
- dwd_order_items 这种 200 万 + 2 个 JOIN,30 分钟
- 解决:接受这个时间,或者用 LOAD DATA INFILE(后面学)

---

## Week 3 项目交付清单

```
03-dwd-layer/
├── README.md                     # DWD 层设计文档
├── ddl/
│   ├── dwd_orders_mysql.sql      # 订单事实表 DDL
│   └── dwd_order_items_mysql.sql # 订单明细事实表 DDL
├── scripts/
│   ├── load_to_dwd.py            # 接入脚本(DDL 内嵌)
│   └── test_dwd.py               # 7 个验证查询
└── queries/
    ├── dwd_queries.sql           # 10 个常用查询
    └── interview_questions.sql   # 6 道面试题
```

---

## 简历故事(Week 3 部分)

> **设计 DWD 层 + 编写 6 道面试 SQL** | [github.com/Three-rgb/ecommerce-data-warehouse](https://github.com/Three-rgb/ecommerce-data-warehouse)
>
> 在电商数仓项目里,负责 ODS → DWD 层的数据加工:
> - 设计维度退化模型,避免下游查询频繁 JOIN
> - 实现业务标记(有效订单/首单)统一分析口径
> - 编写 6 道面试高频 SQL(留存率、转化漏斗、复购率、复购周期、连续登录)
> - 验证数据:7 日留存率 15.5%(符合行业平均),复购周期 60% 集中在 30 天内
>
> **核心收获**:理解了"维度退化""业务标记"在数仓里的实际价值,以及如何用窗口函数解决留存、复购、连续行为等业务问题。

---

## Week 4 准备

### 主题:DWS 层 + Spark 入门

### 目标
- [ ] 主题宽表设计(用户宽表、商品宽表)
- [ ] RFM 模型(用户分层)
- [ ] 累计指标宽表(用户累计金额、累计订单数)
- [ ] PySpark 基础(读 MySQL、写 Parquet)
- [ ] Spark on local mode

### 关键 SQL
- `RANK() / DENSE_RANK()` 排名
- `FIRST_VALUE() / LAST_VALUE()` 边界值
- `NTILE(n)` 分桶
- 累计 SUM OVER 进阶

---

## 经验教训

1. **DDL 内嵌 vs 外部文件**:小项目内嵌,大项目拆分
2. **跨目录 import 不靠谱**:每个脚本自带配置
3. **INSERT 大表要耐心**:不轻易 Ctrl+C
4. **数据造得好,SQL 才简单**:真实业务数据是 SQL 正确的前提

---

**记录时间**:2026-06-18
**作者**:zhao
**Week 3 状态**:完成 ✅
**Week 4 状态**:待开始
