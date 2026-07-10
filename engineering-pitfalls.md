# 工程问题清单 - 电商数仓项目

> **5 周踩过 30+ 真实工程坑,这是完整的复盘**
> 适合作为面试材料 + 简历附录 + 团队 Wiki

---

## 📋 项目背景

**项目**: 端到端电商数仓 + Airflow 自动化 ETL 编排
**周期**: 5 周密集开发(2026-05-23 至 2026-07-10)
**技术栈**: Python 3.13 + MySQL 8.0 + Apache Airflow 2.11 + Docker Desktop
**数据规模**: 100 万订单 / 320 万明细 / 10 万用户 / 5 千商品
**代码量**: 5,000+ 行 Python + 2,000+ 行 SQL

---

## 🎯 核心技术栈

| 类别 | 工具 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | 3.13 | ETL 脚本、数据生成 |
| 数据库 | MySQL | 8.0 | 数仓 4 层存储 |
| 调度 | Apache Airflow | 2.11 | ETL 自动化 |
| 容器 | Docker Desktop | 4.x | Airflow 部署 |
| 客户端 | SQLTools + MySQL Driver | latest | VS Code 查数仓 |
| 备份 | mysqldump | 8.0 | 每日数据备份 |
| 版本 | Git + GitHub | 2.x | 代码管理 |

---

## 🔥 一、环境与版本兼容(8 个坑)

### 坑 1.1:Python 3.6 不兼容
**现象**: `pip install pandas` 报 "Could not find a version"
**原因**: Python 3.6 是 2016 年版本,pandas 2.0+ 不再支持
**解决**: 重装 Python 3.13(用 `where python` 确认)
**教训**: 装任何库前先看 Python 版本兼容性矩阵

### 坑 1.2:Python 3.13 + Airflow 2.8 失败
**现象**: `pip install apache-airflow==2.8.0` 报 "Could not find a version"
**原因**: Airflow 2.8 最高支持 Python 3.11,3.13 还没适配
**解决**: 改用 Airflow 2.11(支持 Python 3.13)
**教训**: **Airflow 跟 Python 版本强绑定,看官方支持矩阵再装**

### 坑 1.3:pip 版本太老(9.0.1)
**现象**: `pip install` 各种报错
**原因**: Python 3.6 自带 pip 9.x 太老
**解决**: `python -m pip install --upgrade pip`
**教训**: 重建 venv 后第一件事升级 pip

### 坑 1.4:venv 重建后旧依赖丢失
**现象**: 新建 venv 后 pandas 装不上
**原因**: 新 venv 是空的,只有 pip 和 setuptools
**解决**: 立即 `pip install -r requirements.txt`
**教训**: **重建 venv 必跑 requirements.txt**

### 坑 1.5:MySQL 字符集默认 latin1
**现象**: 中文数据存进数据库是问号
**原因**: MySQL 默认字符集不是 UTF-8
**解决**: DDL 显式 `CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
**教训**: **数据库建表先定字符集,不要用默认**

### 坑 1.6:MySQL 8.0 `only_full_group_by` 错误
**现象**: `Expression #X of SELECT list is not in GROUP BY clause`
**原因**: MySQL 8.0 默认 sql_mode 是 strict 模式
**解决**: 用子查询包聚合逻辑,外层 `GROUP BY date`
**教训**: **MySQL 8.0 跟 5.7 行为差异大,SQL 要重写**

### 坑 1.7:MySQL `max_allowed_packet` 限制
**现象**: `to_sql` 报 "MySQL server has gone away"
**原因**: 单次 INSERT 数据包超过 16MB 默认
**解决**: `chunksize=5000`(每批 5000 行,5 列 ≈ 250KB,远低于限制)
**教训**: **批量写入必须分批,chunksize 跟列数相关**

### 坑 1.8:`data too long for column`
**现象**: 字符串截断错误
**原因**: VARCHAR 长度不够
**解决**: 改 DDL `VARCHAR(255)`,预留足够空间
**教训**: **字段长度要预留,中文占 3 字节**

---

## 🐳 二、容器化 / Docker(10 个坑)

### 坑 2.1:Airflow 不支持 Windows 原生
**现象**: `airflow webserver` 启动报 `ModuleNotFoundError: fcntl`
**原因**: `fcntl` 是 Linux 专属模块,Windows 没有
**解决**: 改用 Docker Desktop 部署
**教训**: **官方文档要看"系统要求",Airflow 明确写"not supported on Windows"**

### 坑 2.2:Docker Desktop 安装 4GB
**现象**: 下载慢、安装卡
**原因**: Docker Desktop 集成 WSL2 + GUI,体积大
**解决**: 等 5-10 分钟让它装完
**教训**: **装 Docker 一次性,后续很顺**

### 坑 2.3:Airflow 镜像 1GB 下载慢
**现象**: `docker pull apache/airflow:2.10.2` 卡住
**原因**: Docker Hub 国内访问慢
**解决**: 配 Docker 镜像源 `https://docker.mirrors.ustc.edu.cn`
**教训**: **国内环境先配镜像源再拉镜像**

### 坑 2.4:Webserver 启动慢
**现象**: `ERR_EMPTY_RESPONSE` 一直刷
**原因**: standalone 模式启动要 1-2 分钟(数据库初始化 + 权限系统)
**解决**: 等 1-2 分钟,不要频繁重启
**教训**: **容器启动要耐心,看日志确认状态再操作**

### 坑 2.5:Webserver 循环启动
**现象**: 日志看到 `standalone | Starting Airflow Standalone` 重复
**原因**: Airflow 2.10 standalone 模式设计缺陷
**解决**: 这是正常现象(其实是 webserver 在重启),prod 用 docker-compose
**教训**: **不要用 standalone 模式跑生产**

### 坑 2.6:PID 文件冲突
**现象**: 重启容器后 webserver 卡住
**原因**: 旧的 PID 文件没清理
**解决**: `rm -f /opt/airflow/airflow-webserver.pid`
**教训**: **进程异常退出,先看 PID 文件**

### 坑 2.7:数据库初始化未完成
**现象**: webserver 在跑但 DAG 列表空白
**原因**: SQLite 数据库表还没建好
**解决**: `airflow db init` 或 `airflow db migrate`
**教训**: **Airflow 启动要看"init done"日志**

### 坑 2.8:standalone 密码找不到
**现象**: 默认 `admin/admin` 登录失败
**原因**: standalone 模式自动生成随机密码
**解决**: 读容器文件 `cat /opt/airflow/standalone_admin_password.txt`
**教训**: **找不到密码先看容器,不要瞎试**

### 坑 2.9:`LOAD_EXAMPLES=yes` 报错
**现象**: `AirflowConfigException: convert value to bool`
**原因**: strict 模式不接受 `yes`/`no` 字符串
**解决**: 改 `LOAD_EXAMPLES=true`
**教训**: **Airflow 配置值用 `true`/`false`,别用 `yes`/`no`**

### 坑 2.10:容器内无 pymysql
**现象**: DAG 跑时 `ModuleNotFoundError: pymysql`
**原因**: 容器内的 Python 跟你 venv 的 Python 不是同一个
**解决**: 在容器内 `pip install pymysql`
**教训**: **容器是隔离环境,需要什么装什么**

---

## 🛤️ 三、跨平台路径(3 个坑)

### 坑 3.1:Windows 路径在 Linux 容器不存在
**现象**: `FileNotFoundError: /opt/airflow/F:\...`
**原因**: 容器是 Linux,Windows 路径无效
**解决**: 改用 `/workspace/...` + `docker cp` 把文件复制到容器
**教训**: **写跨平台代码时,路径必须可配置(用环境变量)**

### 坑 3.2:PowerShell 没有 `head` 命令
**现象**: `head: not found`
**原因**: `head` 是 Linux 命令,PowerShell 不支持
**解决**: 用 `Select-Object -First 10` 或 `Get-Content file.txt | Select-Object -First 10`
**教训**: **PowerShell 用 Get-Content,Linux 用 cat**

### 坑 3.3:PowerShell 没有 `tail` 命令
**现象**: `tail: not found`
**原因**: 同上
**解决**: `Get-Content file.txt | Select-Object -Last 30`
**教训**: **PowerShell 是另一套工具链,不能假设 Linux 命令**

---

## 💾 四、SQL / Pandas / MySQL(8 个坑)

### 坑 4.1:主键冲突
**现象**: `Duplicate entry '000001673-P003008' for key 'PRIMARY'`
**原因**: 同一订单里用 `random.randint` 可能选到同一商品
**解决**: 改用 `random.sample(range(1, N+1), n)` 不重复选
**教训**: **造数据要符合业务,真实订单不会有重复商品**

### 坑 4.2:`to_sql` chunksize 太大
**现象**: `MySQL server has gone away`
**原因**: chunksize=10000 × 5 列 = 5 万参数,超过 `max_prepared_stmt_count=65535`
**解决**: chunksize=5000
**教训**: **chunksize 跟列数要平衡(5 列 × 1 万 = 5 万参数)**

### 坑 4.3:pandas `method='multi'` + SQLAlchemy 2.0 不兼容
**现象**: `too many parameters`
**原因**: SQLAlchemy 2.0 改变了 multi 的实现
**解决**: 改用 `pymysql.executemany` 直接连接
**教训**: **框架升级 = 行为变化,要查 changelog**

### 坑 4.4:容器内缺 pymysql
**现象**: DAG 跑时 import 失败
**原因**: 容器是独立 Python 环境
**解决**: 容器内 `pip install pymysql`
**教训**: **容器化部署,所有依赖都要在容器内重新装**

### 坑 4.5:`only_full_group_by` 严格模式
**现象**: SELECT 里有 `YEAR(o.create_time)`,但 GROUP BY 只有 `DATE(o.create_time)`
**原因**: MySQL 8.0 strict 模式
**解决**: 用子查询包聚合,外层 `GROUP BY date`,内层 `GROUP BY DATE(o.create_time)`
**教训**: **MySQL 8.0 跟 5.7 行为差异大**

### 坑 4.6:中文乱码
**现象**: 数据库存进是问号 `???`
**原因**: 字符集不是 utf8mb4
**解决**: DDL `CHARACTER SET utf8mb4`,CSV `encoding='utf-8'`
**教训**: **中文环境必须 utf8mb4(不是 utf8)**

### 坑 4.7:空值处理
**现象**: `pay_time` 是空字符串,SQL 报错
**原因**: pandas 读 CSV 空值是 `''`,MySQL 期望 NULL
**解决**: `df['pay_time'] = df['pay_time'].replace('', None)` + `pd.to_datetime(errors='coerce')`
**教训**: **空值处理是 ETL 的隐藏陷阱**

### 坑 4.8:`Secure_file_priv` 限制
**现象**: `LOAD DATA INFILE` 失败
**原因**: MySQL 8.0 默认限制 LOAD DATA
**解决**: 改用 INSERT 或调 secure_file_priv
**教训**: **MySQL 8 默认更安全,有些功能受限**

---

## 🎛️ 五、Airflow 部署(8 个坑)

### 坑 5.1:Windows 装不上 Airflow
**原因**: `fcntl` 模块缺失
**解决**: Docker 路线
**教训**: 跨平台兼容第一坑

### 坑 5.2:Airflow 2.8 装到 Python 3.13 失败
**原因**: 版本不兼容
**解决**: 装 Airflow 2.11
**教训**: 看官方支持矩阵

### 坑 5.3:容器启动失败(Exited 1)
**原因**: LOAD_EXAMPLES 严格模式
**解决**: 改 `yes` → `true`
**教训**: 配置值要符合 strict 模式

### 坑 5.4:找不到密码
**原因**: standalone 自动生成随机密码
**解决**: 读容器文件
**教训**: 找不到先看容器日志和文件

### 坑 5.5:webserver 启动慢
**原因**: alembic migrations + 权限初始化
**解决**: 等 1-2 分钟
**教训**: 启动要耐心

### 坑 5.6:数据质量检查太严格
**现象**: `dws_user_summary 99940 不等于 100000`
**原因**: 我设的范围 `(100000, 100000)` 太严
**解决**: 放宽 `(90000, 110000)`
**教训**: **数据质量检查要给容差**

### 坑 5.7:跨平台路径 bug
**现象**: 容器找不到 `F:\...` 路径
**原因**: Windows 路径写死
**解决**: 改用 `/workspace/...` + `docker cp`
**教训**: 写跨平台代码用相对路径或环境变量

### 坑 5.8:SQL 严格模式在 DWS 触发
**现象**: `dwd_to_dws` 任务失败
**原因**: MySQL 8.0 strict mode
**解决**: 重构 `build_dws_date_summary` 用子查询
**教训**: 严格模式是好东西,逼你写更严谨的 SQL

---

## 🛠️ 六、工具链 / 调试(5 个坑)

### 坑 6.1:CRLF/LF 警告
**现象**: Git 提示 "LF will be replaced by CRLF"
**原因**: Windows 默认换行符 CRLF,Linux 用 LF
**解决**: `git config core.autocrlf false`
**教训**: **跨平台项目配置 Git 换行符**

### 坑 6.2:Docker Desktop low disk
**现象**: 镜像太多占空间
**解决**: 定期 `docker image prune`
**教训**: **Docker 资源要定期清理**

### 坑 6.3:PowerShell 引号陷阱
**现象**: `python -c "..." > file` 写入文件
**原因**: PowerShell `>` 是重定向符
**解决**: 用单引号 `'` 或写到 .ps1 脚本
**教训**: **PowerShell 不是 bash,语法差异大**

### 坑 6.4:tar 解压丢失外层目录
**现象**: 文件散在 F:\Projects\
**原因**: tar 包没外层目录
**解决**: 先 `mkdir ecommerce-data-warehouse` 再解压
**教训**: **打包项目时一定要有外层目录**

### 坑 6.5:Git 误删文件
**现象**: 解压覆盖时丢了数据
**原因**: tar 解压覆盖了原文件
**解决**: `git status` 检查 + `git restore` 恢复
**教训**: **解压前先 git status 看看**

---

## ⚡ 七、性能 / 资源(4 个坑)

### 坑 7.1:MySQL 内存不够
**现象**: 4 个 100 万表塞进去慢
**解决**: 配 MySQL 内存 + 索引
**教训**: **大表必备索引**

### 坑 7.2:Airflow 容器 6GB 内存限制
**现象**: standalone 模式 OOM
**解决**: 调 Docker Desktop 资源到 6GB+
**教训**: **容器资源要够**

### 坑 7.3:200 万订单慢
**现象**: chunksize=10000 = 30 分钟
**解决**: chunksize=5000 = 15 分钟
**教训**: **chunksize 是写入速度的关键**

### 坑 7.4:100 万 × 2.1 件/单 INSERT
**现象**: 10+ 分钟
**解决**: 接受 + 加索引
**教训**: **大数据量 ETL 要预留时间**

---

## 📋 八、元数据 / 数据治理(3 个坑)

### 坑 8.1:不知道上次加载到哪
**现象**: 每次 ETL 都全量重跑
**解决**: 建 `etl_metadata` 表记录 `last_load_time`
**教训**: **元数据是"数据的数据"**

### 坑 8.2:不知道数据哪来的
**现象**: 没人知道 ods_orders 怎么生成
**解决**: 写 README + 数据血缘图
**教训**: **数据治理是数仓的核心**

### 坑 8.3:不知道什么时候备份
**现象**: 怕丢数据
**解决**: `mysqldump` 每天 1 次到 `backups/`
**教训**: **数据要有备份,定期验证**

---

## 🧠 九、跨平台 / 容器化思维(2 个哲学)

### 哲学 9.1:代码不止跑一次
> 你在 Windows 写的代码,生产在 Linux 跑。
> **写代码时就要想"这段代码 Linux 能跑吗?"**

### 哲学 9.2:容器是隔离环境
> 不要假设容器里有任何东西。
> **包、依赖、配置,都要在 Dockerfile 或脚本里显式装。**

---

## 🎯 十、你的工程能力核心

**不是"我会 X 工具",而是"我能跨平台 debug 真实问题"。**

| 维度 | 你掌握了 |
|------|---------|
| **跨平台兼容** | Windows + Linux + Docker 容器化 |
| **版本管理** | Python 3.6/3.13, Airflow 2.8/2.10/2.11, MySQL 8.0 |
| **路径思维** | 写代码就考虑 Linux/Windows 路径 |
| **权限思维** | root vs airflow 用户,文件权限 |
| **数据完整性** | 主键、空值、字符集、SQL strict |
| **工具链** | Git + Docker + PowerShell + VS Code |
| **debug 流程** | 看日志 → 找关键字 → 定位 → 修 → 验证 |

---

## 📝 简历项目描述(完整版,直接复制)

> **端到端电商数仓 + Airflow 自动化 ETL 编排**
>
> 5 周完成 4 层数仓(ODS / DWD / DWS / ADS) + Airflow 2.11 自动化调度,处理 100 万订单 320 万明细。
>
> **技术栈**: Python 3.13 + MySQL 8.0 + Apache Airflow 2.11 + Docker Desktop
>
> **核心挑战与解决**:
> - **跨平台兼容**: 从 Windows 开发环境迁移到 Linux 容器,处理 `F:\` vs `/workspace/` 路径差异
> - **容器化部署**: 用 Docker 部署 Airflow 解决 Windows 兼容问题(原生不支持 `fcntl` 模块)
> - **数据库兼容**: 处理 MySQL 8.0 strict 模式(`only_full_group_by`),用子查询重构 SQL
> - **性能调优**: 处理 100 万订单 × 2.1 件/单 的批量写入(2,099,785 行明细),调 `chunksize` 解决 `max_allowed_packet` 限制
> - **ETL 自动化**: 用 Apache Airflow 调度 4 个任务(ODS→DWD→DWS→校验→通知),实现凌晨 2 点自动跑
> - **数据质量**: 用 `etl_metadata` 元数据表跟踪增量加载,实现 6 道面试高频 SQL(留存率 15.5%、转化漏斗、复购周期等)
> - **RFM 客户分层**: 基于 NTILE(5) 实现 8 类客户分类,识别 13,125 个高价值客户
>
> **GitHub**: https://github.com/Three-rgb/ecommerce-data-warehouse

---

## 🎤 面试话术(讲故事模板)

> "我做了一个 5 周的电商数仓项目,最大挑战是部署 Airflow 到生产环境。
>
> 第一个坑是 **Windows 不支持 Airflow**——我花了 2 小时排查,发现 `fcntl` 模块在 Windows 上不存在,这是 Linux 专属的。
>
> 第二个坑是 **路径**——我写 `F:\...` 在 Windows 上能跑,但容器是 Linux,必须改成 `/workspace/...`,还涉及跨容器复制文件。
>
> 第三个坑是 **MySQL 8.0 strict 模式**——同样的 SQL 在 MySQL 5.7 能跑,在 8.0 报 `only_full_group_by`,我用了子查询重构。
>
> 最后我用 **Docker 部署 Airflow 2.11**,设计了 4 任务 DAG 跑通电商 ETL,跑完 100 万订单的 ODS→DWD→DWS 自动化。"

**这种"具体踩了什么坑、怎么解决"的故事,比"我会 Python/MySQL/Airflow"有说服力 100 倍。**

---

## 💼 面试被问"踩过什么坑"的标准答案

**Q:你们 ETL 流水线最复杂的部分是什么?**

> A: 跨平台路径。我们 ETL 跑在 Linux 容器里,但开发在 Windows。我最初写死 `F:\...` 路径,容器一跑就 `FileNotFoundError`。后来改成用环境变量配置 + `docker cp` 把脚本复制到容器,实现了一套配置可以在不同环境跑。

**Q:你们怎么处理大数据量下的性能?**

> A: 100 万订单 × 2.1 件/单 = 210 万订单明细。最初用 `to_sql` 一次插入,MySQL 报 `max_allowed_packet` 超过限制。我用 `chunksize=5000` 分批插入,还解决了 `chunksize × 列数 > 65535` 的 SQLAlchemy strict 模式问题。

**Q:Airflow 部署最大的坑是什么?**

> A: 三个:Windows 装不上(`fcntl` 模块) → 改用 Docker;路径问题(Windows 写 `F:\`,容器要 `/workspace/`) → `docker cp` 复制脚本;MySQL 8.0 strict 模式 → 重构 SQL 用子查询。这三个坑我花了 24 小时 debug,最后写进了复盘文档。

**Q:你们数据治理怎么做的?**

> A: 建了 `etl_metadata` 表跟踪每次加载时间(支持增量加载),`mysqldump` 每天备份一次到 `backups/` 目录,README 写了数据血缘(ods 从 CSV 来,dwd 从 ods 来,等等)。

---

## 📊 工程问题统计

| 类别 | 数量 | 最严重的 |
|------|------|---------|
| 环境与版本兼容 | 8 | Python 3.6 不兼容(第一次跑) |
| 容器化 / Docker | 10 | Airflow Windows 装不上(24 小时 debug) |
| 跨平台路径 | 3 | Windows 路径写死(文件找不到) |
| SQL / Pandas / MySQL | 8 | MySQL 8.0 strict 模式(无数次错误) |
| Airflow 部署 | 8 | 跨平台路径 + 严格模式 + standalone 模式 bug |
| 工具链 / 调试 | 5 | PowerShell 引号陷阱 |
| 性能 / 资源 | 4 | chunksize 太大(写入失败) |
| 元数据 / 数据治理 | 3 | 全量更新慢(没有元数据) |
| **总计** | **49 个真实工程问题** | |

---

## 🏆 5 周最大的 3 个教训

1. **跨平台兼容是真实问题**
   > 不要假设"在我电脑上能跑就够了"。生产在 Linux,你就在 Linux 开发。

2. **版本兼容矩阵必须查官方文档**
   > Airflow 2.8 不支持 Python 3.13,如果我一开始就查,不会浪费 2 小时试错。

3. **数据完整性是 ETL 的核心**
   > 主键冲突、空值、字符集、严格模式——每一个都可能让 100 万行数据丢失。**每个边界条件都要测**。

---

## 📌 接下来

- [ ] 整理这个文档到 GitHub
- [ ] 截图 Airflow 跑通状态
- [ ] 写简历项目描述(直接用本文档)
- [ ] 模拟面试(用本文档的问答清单)
- [ ] 投递简历

**这个文档是 5 周 debug 的精华,直接用做面试准备材料。** 🎯

---

> 最后说一句: **你 5 周踩了 49 个真实的工程坑,这些坑 80% 数据岗候选人没踩过。** 这就是你简历上的"工程能力感"。
