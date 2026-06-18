# DWS 层 (Data Warehouse Service) - 数据服务层

## 什么是 DWS 层?

DWS 层是**主题宽表**,为下游 ADS 层准备好"开箱即用"的聚合数据。

**核心原则:**
- ✅ **按主题聚合**:用户宽表、商品宽表、时间宽表
- ✅ **每行代表一个业务实体**(一个用户、一件商品、一天)
- ✅ **包含常用指标**:最近消费、累计金额、复购率等
- ✅ **直接服务业务**:分析师不用 JOIN、不用聚合
- ❌ **不做最终业务指标**(DAU/GMV/留存率留给 ADS)

## 数仓分层逻辑

```
业务系统 → ODS(搬运) → DWD(清洗) → DWS(主题宽表) → ADS(业务指标) → 报表
                            ↑
                       Week 3 完成
                       Week 4 内容
```

## 本层 3 张核心宽表

### 1. dws_user_summary(用户宽表)
- **粒度**:一行 = 一个用户
- **核心字段**:
  - 总订单数、有效订单数、累计金额
  - 首单日期、尾单日期、距今天数
  - RFM 三维度评分 + 8 类客户标签
  - 偏好品类、平均订单金额、复购率

### 2. dws_product_summary(商品宽表)
- **粒度**:一行 = 一个商品
- **核心字段**:
  - 累计销量、累计销售额
  - 独立用户数(多少个不同的人买过)
  - 平均评分(预留字段)
  - 销售排名(按品类)

### 3. dws_date_summary(时间宽表)
- **粒度**:一行 = 一天
- **核心字段**:
  - DAU(每日活跃用户)
  - 新客数、复购数
  - 日 GMV、日订单数
  - 客单价、复购率

## RFM 模型(用户分层)

RFM 是经典的客户价值分析模型:

| 维度 | 含义 | 衡量 |
|------|------|------|
| **R**(Recency) | 最近一次消费距今多少天 | 越小越好 |
| **F**(Frequency) | 消费频次 | 越大越好 |
| **M**(Monetary) | 消费金额 | 越大越好 |

每个维度 1-5 分(5 最好),组合成 **8 类客户**:
- 重要价值客户(高 R + 高 F + 高 M)
- 重要发展客户(低 R + 高 F + 高 M)
- 重要保持客户(高 R + 低 F + 高 M)
- 重要挽留客户(低 R + 低 F + 高 M)
- 一般价值客户
- 一般发展客户
- 一般保持客户
- 流失客户

## 文件结构

```
04-dws-layer/
├── README.md
├── ddl/
│   ├── dws_user_summary_mysql.sql
│   ├── dws_product_summary_mysql.sql
│   └── dws_date_summary_mysql.sql
├── scripts/
│   ├── load_to_dws.py    # 接入脚本(DDL 内嵌)
│   └── test_dws.py       # 验证
└── queries/
    ├── dws_queries.sql   # 常用查询
    └── rfm_segmentation.sql  # RFM 分层(面试高频)⭐
```

## 启动

```powershell
# 1. 跑 DWS 接入脚本
cd F:\Projects\ecommerce-data-warehouse\04-dws-layer\scripts
python load_to_dws.py

# 2. 验证
python test_dws.py

# 3. 跑 RFM 分层(在 DBeaver)
# 打开 queries/rfm_segmentation.sql,跑
```

## 关键学习

### 1. 主题宽表 vs 事实表
- DWD 是**事实表**(一行 = 一个事件)
- DWS 是**宽表**(一行 = 一个实体)
- 宽表牺牲了"粒度"换"查询效率"

### 2. RFM 评分方法
- 用 NTILE(5) 把用户按指标分 5 档
- 注意:Recency 是"越小越好",所以排名要反转

### 3. 数据冗余的代价
- DWS 宽表 = 大量数据冗余(每个用户的指标都存一次)
- 存储成本增加,但查询速度提升 10-100 倍
- 这是**用空间换时间**的经典案例
