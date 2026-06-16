# 学习日志 - 电商数仓项目

> 从 0 基础到 MySQL 数仓的 4 小时实战记录
> 适合作为简历项目故事 + 个人成长复盘

---

## 项目概览

**目标**:搭建一个端到端的电商数仓项目,覆盖数据生成 → 数仓分层 → ETL → 调度,用于求职作品集。

**技术栈**:
- Python 3.13 + pandas + Faker
- MySQL 8.0(数据仓库)
- Git + GitHub(版本管理)
- PyCharm(开发环境)

**数据规模**:
| 表 | 行数 |
|---|---|
| ods_users | 100,000 |
| ods_products | 5,000 |
| ods_orders | 1,000,000 |
| ods_order_items | 2,099,785 |
| **合计** | **3,204,785** |

---

## Week 1 复盘:造数据(完成 ✅)

### 完成了什么

- [x] 100 万订单数据生成
- [x] 10 万用户 + 5 千商品 + 200 万订单明细
- [x] PyCharm 解释器配置
- [x] 数据探索脚本(explore.py)
- [x] Git 仓库初始化 + 首次提交
- [x] GitHub 推送(Clash Verge 代理 7897)

### 数据特征

```
订单状态分布:
  paid      649,339 (64.93%)  ← 已支付
  shipped   150,231 (15.02%)  ← 已发货
  received  100,469 (10.05%)  ← 已收货
  cancelled  50,100 ( 5.01%)  ← 已取消
  refunded   49,861 ( 4.99%)  ← 已退款

客单价:897.96 元
时间跨度:2025-06-15 ~ 2026-06-16(366 天)
```

### 关键学习

1. **Faker 库生成仿真数据** — 用 `Faker('zh_CN')` 生成中文姓名、城市、手机号
2. **随机数种子** — `random.seed(42)` 让数据可复现
3. **对数正态分布** — 模拟真实价格分布(便宜的多,贵的少)
4. **业务逻辑权重** — `random.choices` 用权重控制状态分布

---

## Week 2 复盘:ODS 层(完成 ✅)

### 完成了什么

- [x] MySQL 8.0 数据仓库搭建
- [x] ODS 层 4 张表设计(DDL + 索引)
- [x] 数据接入脚本(纯 pymysql,绕开 SQLAlchemy 兼容性坑)
- [x] 数据验证脚本(7 个查询)
- [x] DBeaver 可视化连接
- [x] mysqldump 数据备份(360 MB)
- [x] Week 2 全部代码推 GitHub

### MySQL 表结构

```sql
ods_users      -- 用户表,10万行
ods_products   -- 商品表,5千行
ods_orders     -- 订单主表,100万行
ods_order_items -- 订单明细,200万行
```

**关键设计**:
- 字符集:`utf8mb4`(支持 emoji)
- 引擎:`InnoDB`(支持事务)
- 索引:`user_id`、`create_time`、`status` 等常用查询字段
- 主键:`ods_order_items` 是 `(order_id, product_id)` 联合主键

### 关键学习

1. **SQLAlchemy + pandas to_sql 的坑**:
   - `method="multi"` 在 SQLAlchemy 2.0 下实现有变化
   - 容易触发 MySQL `max_prepared_stmt_count` 限制
2. **pymysql executemany 更稳** — 自己控制 batch size
3. **MySQL 字符集**:`utf8mb4` 才是真正的 UTF-8(支持 emoji 和生僻字)
4. **数据完整性约束**:主键冲突 = 数据脏

---

## 今日 Debug 实战:7 个真实问题

这是最有价值的部分——记录今天遇到并解决的真实问题。

### 问题 1:C 盘空间不足,项目放哪?

**现象**:C 盘快满了,Python 装在 C 盘,venv 也在 C 盘。

**解决**:统一规划到 F 盘
```
F:\Projects\ecommerce-data-warehouse\    # 项目代码
F:\DataEng\venv\ecommerce\                # 虚拟环境
F:\DataEng\mysql_data\                    # MySQL 数据(后续)
F:\Workspace\generated\                   # 临时数据(后续)
```

**经验**:**C 盘只放系统,数据/开发/项目都放数据盘**。这是开发规范。

---

### 问题 2:tar.gz 解压后目录结构乱了

**现象**:解压后文件直接散在 `F:\Projects\`,没在 `ecommerce-data-warehouse/` 子目录里。

**原因**:`tar -xzf` 解压时,如果 .tar.gz 文件里的最外层就是文件(没有父目录),会直接散开。

**解决**:用 PowerShell 一行 `Move-Item` 整理:
```powershell
New-Item -ItemType Directory -Path "F:\Projects\ecommerce-data-warehouse" -Force
Get-ChildItem "F:\Projects" | Move-Item -Destination "F:\Projects\ecommerce-data-warehouse\"
```

**经验**:**Windows 上 tar 解压行为不一致**,最好用 7-Zip 或在 PowerShell 里操作。

---

### 问题 3:Python 版本太老,装不上 pandas

**现象**:`pip install pandas` 报 "Could not find a version that satisfies the requirement pandas>=2.0.0"。

**根本原因**:`python --version` 显示 `Python 3.6.0`(2016 年的版本),pandas 2.0+ 不支持。

**解决**:
- 发现 `C:\Users\赵梦龙\AppData\Local\Programs\Python\Python313\` 已经有 Python 3.13
- 用 3.13 重建 venv
- pip 升级到 21.3.1,setuptools 升级到 59.6.0

**经验**:**先 `python --version` 再装包**。版本不匹配是 90% 装包失败的根因。

---

### 问题 4:Git push 失败(网络)

**现象**:`git push` 报 `Connection was reset`。

**原因**:
- 浏览器走代理能访问 GitHub
- PowerShell 里的 `git` 不会自动用浏览器代理
- 同时 URL 写错了(`rgbthree` 应该是 `Three-rgb`)

**解决**:
```powershell
git remote remove origin
git remote add origin https://github.com/Three-rgb/ecommerce-data-warehouse.git
git config --global http.proxy http://127.0.0.1:7897  # Clash Verge
git config --global https.proxy http://127.0.0.1:7897
git push -u origin main
```

**经验**:**GitHub 国内访问需要代理,但需要单独给 Git 配**。

---

### 问题 5:venv 里缺 pandas

**现象**:跑 `load_to_mysql.py` 报 `ModuleNotFoundError: No module named 'pandas'`。

**原因**:用 Python 3.13 重建 venv 时是空的,后来只装了 sqlalchemy + pymysql,没装 pandas。

**解决**:在 venv 里 `pip install -r requirements.txt` 一次性装齐。

**经验**:**重建 venv 后第一件事就是装齐 requirements.txt**。

---

### 问题 6:SQLAlchemy 2.0 chunksize 兼容性问题

**现象**:`load_to_mysql.py` 跑 200 万订单明细时报 "too many parameters"。

**原因分析**:
- `pandas.to_sql(method="multi", chunksize=20000)` 生成 `INSERT ... VALUES (?, ?, ...)`
- 20000 × 5 列 = 100,000 参数
- MySQL `max_prepared_stmt_count` 默认 65,535 → 超出

**尝试解决**:
- chunksize 5000 → 仍然报错(可能是 SQLAlchemy 2.0 内部实现变化)
- 5000 × 5 = 25,000 应该不超,但 SQLAlchemy 实际生成更多参数

**最终解决**:**放弃 SQLAlchemy,直接用 pymysql executemany**,完全控制 batch size:
```python
cursor.executemany(insert_sql, batch)  # batch = 1000 行
```

**经验**:**遇到工具链兼容性问题,不要死磕,换更底层的工具**。pymysql 虽老但稳定。

---

### 问题 7:数据生成 bug — 订单明细主键冲突 ⭐

**现象**:`pymysql.err.IntegrityError: (1062, "Duplicate entry '000001673-P003008' for key 'ods_order_items.PRIMARY'")`

**根本原因**:`generate_orders.py` 用 `random.randint(1, N_PRODUCTS)` 选商品,可能选到同一个商品多次:
```python
# 旧代码(有 bug)
for _ in range(n_items):
    product_id = f"P{random.randint(1, N_PRODUCTS):06d}"  # ← 可能重复!
```

**业务现实**:同一订单里同一商品应该只出现 1 行,数量在 `quantity` 字段体现。

**修复**:用 `random.sample` 不重复选:
```python
# 修复后
selected_product_ids = random.sample(range(1, N_PRODUCTS + 1), n_items)
for product_id_int in selected_product_ids:
    product_id = f"P{product_id_int:06d}"
```

**教训**:
1. **数据生成要符合业务约束**,不是随机就行
2. **主键约束是发现数据 bug 的好工具**
3. **修复后必须重新造数据**(修脚本不修数据,问题还在)

---

## 完整的修复-重试-再修复流程

```
生成数据
   ↓
ODS 接入(失败:路径错)
   ↓ 修复
ODS 接入(失败:缺 pandas)
   ↓ 修复
ODS 接入(失败:chunksize 太大)
   ↓ 修复
ODS 接入(失败:chunksize 还是太大)
   ↓ 换工具
ODS 接入(失败:数据主键冲突)
   ↓ 修脚本 + 重新造数据
ODS 接入(成功!)
   ↓
验证查询
   ↓
DBeaver 可视化
   ↓
mysqldump 备份
   ↓
git commit + push
```

**这是真实数据工程师的日常工作流程**。教科书上不会教你这些。

---

## 心法总结

### 1. 遇到错误先看完整报错
```
错误信息 + 错误位置 + 调用栈
↓
搜报错关键信息(用 Google/Stack Overflow)
↓
对照自己代码
```

### 2. 不要急着改代码,先理解问题
- 第一次报"too many parameters" → 我以为是 chunksize
- 第二次还报 → 才意识到可能是 SQLAlchemy 2.0 兼容性问题
- 第三次报"Duplicate entry" → 才发现是数据本身的 bug

**多看几次报错,问题会自己浮出水面。**

### 3. 工具链的兼容性是真实工程的坑
- pandas + SQLAlchemy + MySQL 8.0 + Python 3.13,每个新版本都可能引入新问题
- 遇到奇怪问题,先怀疑"是不是新版本不兼容"
- 必要时换更底层的工具(pymysql 替代 SQLAlchemy)

### 4. 数据是真实业务的反映
- 造数据不能瞎 random,要知道业务上是不是合理
- "一个订单里同一商品出现两次"是 bug,不是数据问题
- **主键、外键、唯一索引**是数据完整性的护城河

### 5. 路径和环境配置是 Windows 的痛
- 改 PATH、装 Python、激活 venv...Windows 比 Linux 多 10 倍坑
- **虚拟环境是必须的**,不要把包装到系统 Python

---

## 简历故事模板

> **端到端电商数仓项目** | [github.com/Three-rgb/ecommerce-data-warehouse](https://github.com/Three-rgb/ecommerce-data-warehouse)
>
> **项目背景**:为求职作品集,独立设计并实现了一个完整的电商数仓,覆盖数据生成、ETL、数仓分层、调度编排全流程。
>
> **技术栈**:Python 3.13 + pandas + MySQL 8.0 + SQLAlchemy + Git
>
> **项目内容**:
> - 用 Python + Faker 设计数据生成器,产出 100 万订单测试数据(用户、商品、订单、订单明细 4 张表,共 320 万行)
> - 设计 ODS 层表结构(InnoDB 引擎 + utf8mb4 字符集 + 业务主键)
> - 用 SQLAlchemy + pymysql 实现数据接入,处理了 MySQL `max_prepared_stmt_count` 限制和数据主键冲突等多个工程问题
> - 用 mysqldump 实现每日数据备份
> - 用 Git + GitHub 做完整版本管理
>
> **核心收获**:
> - 理解了数仓分层(ODS/DWD/DWS/ADS)的实际意义
> - 解决了 SQLAlchemy 2.0 + MySQL 8.0 的多个兼容性问题
> - 学会了在数据接入时进行数据质量检查(主键约束、字段类型)
> - 体验了真实的 debug 流程:从环境配置到工具兼容性到数据本身的问题

---

## 下一步计划

### Week 3:DWD 层(数据清洗) ⏳
- 维度建模基础
- 缓慢变化维(SCD)
- 数据清洗:去重、空值、异常值
- 窗口函数:ROW_NUMBER、LAG、LEAD、SUM OVER
- 留存率、漏斗、复购分析(面试必考)

### Week 4:DWS 层 + Spark 入门
- 主题宽表设计
- 轻度聚合(用户最近一次消费、累计金额、复购周期)
- PySpark 基础
- Spark on local mode

### Week 5:ADS 层 + Airflow
- 业务指标宽表(DAU、GMV、RFM)
- Airflow DAG 设计
- 任务调度

### Week 6:K8s + 部署
- 容器化
- Spark on K8s
- 监控告警

---

## 项目亮点(可以讲给面试官听)

1. **真实场景驱动**:不是 toy project,是完整的电商业务
2. **数据规模真实**:320 万行,SQL 调优有实际意义
3. **遇到并解决多个真实问题**:
   - 跨平台环境配置
   - 工具链兼容性
   - 数据完整性
4. **完整的工程实践**:Git、备份、文档、代码规范

---

## 资源链接

- GitHub: https://github.com/Three-rgb/ecommerce-data-warehouse
- 项目文档: `docs/learning-log.md`(本文)
- MySQL 备份: `backups/ecommerce_dw_*.sql`

---

**记录时间**:2026-06-16
**作者**:zhao
**项目状态**:Week 1 + Week 2 完成,Week 3 待开始
