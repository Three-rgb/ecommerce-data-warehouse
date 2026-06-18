# DWD 层 (Data Warehouse Detail) - 数据明细层

## 什么是 DWD 层?

DWD 层是**数仓的清洗层**,在 ODS 基础上做轻度规范化,但**不聚合**。

**核心原则:**
- ✅ **数据清洗**:去重、空值、异常值处理
- ✅ **维度退化**:把维度字段冗余到事实表,减少 JOIN
- ✅ **业务规则**:过滤无效数据(已取消、已退款)
- ✅ **保持粒度**:一行 = 一个业务事件(订单不变)
- ❌ **不聚合**:不计算指标(留给 DWS)

## 数仓分层逻辑回顾

```
业务系统(原始数据)
   ↓  [ODS 层]  - 原封不动搬进来
原始数据存储(MySQL ods_*)
   ↓  [DWD 层]  - 清洗 + 规范化 + 维度退化  ← 本周内容
明细数据(MySQL dwd_*)
   ↓  [DWS 层]  - 主题宽表、用户/商品聚合
主题宽表(下周内容)
   ↓  [ADS 层]  - 业务指标
DAU/GMV/留存(再下周)
```

## 本层文件结构

```
03-dwd-layer/
├── README.md                 # 本文档
├── ddl/
│   ├── dwd_orders_mysql.sql  # DWD 订单事实表
│   └── dwd_order_items_mysql.sql  # DWD 订单明细
├── scripts/
│   ├── load_to_dwd.py        # ODS → DWD 接入脚本
│   └── test_dwd.py           # 验证脚本
└── queries/
    ├── dwd_queries.sql       # 10 个 DWD 常用查询
    └── interview_questions.sql  # 面试题:留存/漏斗/复购
```

## DWD 表设计

### dwd_orders(订单事实表)

```
原始 ods_orders + 用户/商品信息(维度退化)
```

字段:
```sql
- order_id, user_id, order_amount, status, create_time, pay_time
+ username, age, city, level  (从 ods_users 退化)
+ is_valid_order  (业务规则:paid/shipped/received)
+ order_date, order_hour  (时间分桶)
+ is_first_order  (用户级标记:首单/非首单)
```

### dwd_order_items(订单明细事实表)

```
原始 ods_order_items + 商品信息(维度退化)
```

字段:
```sql
- order_id, product_id, quantity, unit_price, amount
+ product_name, category, sub_category, brand  (从 ods_products 退化)
+ order_time  (从 dwd_orders 退化)
+ is_valid_order  (业务规则)
```

## 业务规则

### 有效订单(用于业务分析)
- `paid` - 已支付
- `shipped` - 已发货
- `received` - 已收货

### 无效订单(过滤掉)
- `cancelled` - 已取消(不计入 GMV)
- `refunded` - 已退款(不计入留存)

**为什么 refunded 不算留存?**
- 用户退了,说明这单对他没价值
- 把他当留存客户是误导业务

## 启动

```powershell
# 1. 装好依赖(如果之前没装)
pip install sqlalchemy pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 跑 DWD 接入脚本
cd F:\Projects\ecommerce-data-warehouse\03-dwd-layer\scripts
python load_to_dwd.py

# 3. 验证
python test_dwd.py

# 4. 跑面试题
# 打开 queries/interview_questions.sql,在 DBeaver 里执行
```

## 关键技术点

### 1. 维度退化
```sql
-- 不好:每次查询都要 JOIN
SELECT o.*, u.username
FROM ods_orders o
JOIN ods_users u ON o.user_id = u.user_id;

-- 好:把 username 退化到 dwd_orders
SELECT * FROM dwd_orders;  -- 直接有 username
```

### 2. 首单标记
```sql
-- 用窗口函数判断首单
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY create_time) = 1
```

### 3. 留存率
```sql
-- 7 日留存:首单后 1-7 天内又下过单的用户
DATEDIFF(create_time, first_order_date) BETWEEN 1 AND 7
```

详见 `queries/interview_questions.sql`。
