# ODS 层 MySQL 版使用指南

## 优势

MySQL 版:
- ✅ 贴近真实生产环境
- ✅ DBeaver 可视化查数据
- ✅ 支持并发访问(多用户同时查)
- ✅ 完整的事务支持
- ✅ 后面 Spark 直接读 MySQL 数据

## 环境要求

- MySQL 8.0+ (3306 端口)
- Python 包: pymysql, sqlalchemy
- 用户: root (密码在 db_config.py)

## 启动步骤

### 1. 装 Python 包

```powershell
# 激活虚拟环境
F:\DataEng\venv\ecommerce\Scripts\Activate.ps1

# 装 SQLAlchemy + pymysql
pip install sqlalchemy pymysql -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 同步 MySQL 版文件

下载项目包,确保 `02-ods-layer/` 下有:
- `scripts/db_config.py`       ← 新增
- `scripts/load_to_mysql.py`   ← 新增
- `scripts/test_ods_mysql.py`  ← 新增
- `ddl/ods_*_mysql.sql`        ← 新增(MySQL 语法)

### 3. 配置数据库连接

打开 `scripts/db_config.py`,确认:
```python
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",   # ← 改成你的密码
    "charset": "utf8mb4",
}
```

### 4. 跑数据接入

```powershell
cd F:\Projects\ecommerce-data-warehouse\02-ods-layer\scripts
python load_to_mysql.py
```

预期输出:
```
[1/4] 创建数据库 ecommerce_dw...
[2/4] 创建表结构...
[3/4] 导入 CSV 数据
  → users.csv → ods_users     (10万,几秒)
  → products.csv → ods_products (5千,1秒)
  → orders.csv → ods_orders   (100万,30秒-1分钟)
  → order_items.csv → ods_order_items (200万,1-2分钟)

📊 ecommerce_dw 数据库表数据汇总
  ods_users                 100,000 行
  ods_products                5,000 行
  ods_orders               1,000,000 行
  ods_order_items          2,099,219 行

✅ 完成!
```

### 5. 跑验证

```powershell
python test_ods_mysql.py
```

会跑 7 个查询,展示数据分布和质量。

### 6. 在 DBeaver 里看数据

1. DBeaver → 新建连接 → MySQL
2. 填连接信息:
   - Host: localhost
   - Port: 3306
   - Database: ecommerce_dw
   - User: root
   - Password: 123456
3. 测试连接 → 完成
4. 左侧导航就能看到 `ecommerce_dw` 下的 4 张表
5. 双击表名 → 看数据(前 200 行)
6. 右键 → "SQL 编辑器" → 写查询

## 性能参考

| 数据量 | 导入耗时 | 查询耗时(简单) |
|--------|----------|-----------------|
| 10 万用户 | 5 秒 | < 0.1 秒 |
| 5 千商品 | < 1 秒 | < 0.1 秒 |
| 100 万订单 | 30-60 秒 | 1-3 秒 |
| 200 万订单明细 | 60-120 秒 | 2-5 秒 |

100 万订单的导入时间取决于机器性能。InnoDB 引擎会写 binlog,稍慢但安全。

## MySQL 特有优化(后续)

- **主键**:已加
- **索引**:常用查询字段都加了
- **分区**(超大数据量时):可按 create_time 月分区
- **列式存储**:MySQL 8 不支持,需要 ClickHouse 或 Doris
- **后续可考虑**:TiDB(分布式 MySQL 兼容)

## 常见问题

**Q: 报错 "Access denied for user 'root'"?**
A: 密码错。在 db_config.py 里改成对的。

**Q: 报错 "Can't connect to MySQL server"?**
A: MySQL 服务没启动。`net start mysql` 或在服务管理器里启动。

**Q: 导入太慢?**
A: 改 load_to_mysql.py 里的 `chunksize=10000` 调大(如 50000),用 `method="multi"`。

**Q: 中文乱码?**
A: charset 已经是 utf8mb4。如果还有问题,检查 MySQL 服务器配置:
```sql
SHOW VARIABLES LIKE 'character_set%';
```

## 下一步

- Week 3:进入 DWD 层(数据清洗、规范化)
- Week 4:用 Spark 重写 ETL
- Week 5:Airflow 调度
