# 电商数仓项目 E-Commerce Data Warehouse

一个**端到端的数据仓库项目**,模拟真实电商业务场景,完整覆盖:

- 数据生成(造数据)
- ODS → DWD → DWS → ADS 四层建模
- Spark 分布式 ETL
- Airflow 调度编排
- 业务指标产出

## 项目结构

```
ecommerce-data-warehouse/
├── 01-data-generation/      # 用 Python Faker 造 100 万订单数据
├── 02-ods-layer/            # 原始数据层,数据接入
├── 03-dwd-layer/            # 清洗明细层,数据去重、规范化
├── 04-dws-layer/            # 轻度聚合层,主题宽表
├── 05-ads-layer/            # 应用层,业务指标
├── 06-spark-etl/            # 用 Spark 重写核心 ETL
├── 07-airflow-dag/          # 调度编排
├── data/                    # 生成的原始数据
└── docs/                    # 笔记与文档
```

## 数据规模

| 表 | 条数 | 说明 |
|---|---|---|
| 用户表 | 10 万 | 过去 2 年注册 |
| 商品表 | 5 千 | 5 个大类 |
| 订单表 | 100 万 | 过去 1 年 |
| 订单明细 | 200-500 万 | 1 单 1-5 件商品 |
| 行为日志 | 500 万 | 点击/收藏/加购(可选) |

## 技术栈

- **Python 3.8+** + pandas + Faker
- **MySQL 8.0** 或 PostgreSQL
- **Hive**(后续替换 MySQL)
- **Spark 3.x + PySpark**
- **Airflow 2.x**
- **K8s**(第 6 周开始)

## 学习路径

| 周 | 任务 | 产出 |
|---|---|---|
| Week 1 | 造数据 + 项目搭建 | 100 万订单数据 |
| Week 2 | ODS + DWD 层 | 清洗后的明细表 |
| Week 3 | DWS + ADS 层 | 业务指标宽表 |
| Week 4 | Spark 重写 ETL | PySpark 任务 |
| Week 5 | Airflow 调度 | DAG 跑通 |
| Week 6 | K8s 部署 | 容器化 |

## 业务指标(ADS 层最终产出)

- DAU / MAU
- 次日 / 7 日 / 30 日留存率
- GMV / 客单价
- 复购率
- 转化漏斗(浏览→加购→下单→支付)
- RFM 用户分层
- 商品销售 Top 榜

## 快速开始

```bash
# 1. 装依赖
pip install -r requirements.txt

# 2. 一键造数据
cd 01-data-generation
python run_all.py

# 3. 数据会生成在 ../data/ 目录
ls -lh ../data/
```
