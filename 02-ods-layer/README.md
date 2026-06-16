# ODS 层 (Operational Data Store) - 原始数据层

## 什么是 ODS 层?

ODS(Operational Data Store)是数据仓库的第一层,**几乎不做任何数据加工**,把业务系统的原始数据原封不动搬进来。

**核心原则:**
- ✅ **保留原始结构**:字段名、类型、空值都要保持原样
- ✅ **全量快照**:每次接入都全量,不做增量删除
- ✅ **可追溯**:能从 ODS 还原业务系统的原始数据
- ❌ **不做的**:不脱敏、不去重、不改字段名、不聚合

## 为什么需要 ODS 层?

```
业务系统 (MySQL/Postgres/CSV/日志)
   ↓
   ↓ 原始数据,不加工
   ↓
ODS 层 (我们这里用 DuckDB)
   ↓
   ↓ 清洗、规范化
   ↓
DWD 层 (下周内容)
```

**价值:**
1. **数据可追溯** — 出问题能从 ODS 回到原始数据
2. **数据隔离** — 业务库查询不影响分析
3. **统一格式** — 不同来源的数据先放一起,再清洗
4. **审计合规** — 原始数据保留,改动可追溯

## 本层文件结构

```
02-ods-layer/
├── README.md              # 本文档
├── ddl/                   # 表结构定义
│   ├── ods_users.sql
│   ├── ods_products.sql
│   ├── ods_orders.sql
│   └── ods_order_items.sql
├── scripts/               # 数据接入脚本
│   └── load_to_duckdb.py  # 把 CSV 导入 DuckDB
├── queries/               # 常用查询模板
│   └── ods_queries.sql
└── ods.duckdb             # DuckDB 数据库文件(自动生成,不入 Git)
```

## 数据接入流程

1. 业务系统产生数据 (CSV/DB/Log)
2. 通过 `load_to_duckdb.py` 导入到 DuckDB
3. 用 SQL 在 DuckDB 上做查询(只读,不改数据)
4. 后续 DWD 层从这里取数

## 技术栈

- **DuckDB 0.10+** - 嵌入式分析数据库
- **Python 3.13+**
- **pandas 2.x** - 数据验证

## 启动

```powershell
# 1. 装 DuckDB
pip install duckdb -i https://pypi.tuna.tsinghua.edu.cn/simple

# 2. 跑数据接入脚本
cd F:\Projects\ecommerce-data-warehouse\02-ods-layer\scripts
python load_to_duckdb.py

# 3. 验证(交互式)
python -c "import duckdb; con = duckdb.connect('../ods.duckdb'); print(con.execute('SHOW TABLES').df())"
```
