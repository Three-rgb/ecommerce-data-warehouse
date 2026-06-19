# Week 5 复盘 - Airflow 调度编排

> 从"装不上"到"自动跑通" — 9 小时 6 个真实问题
> 适合作为简历项目故事 + 个人成长复盘

---

## 核心成就

✅ Docker Desktop 部署
✅ Apache Airflow 2.10.2 容器化
✅ Web UI 登录(找到 standalone 密码)
✅ **hello_world DAG 跑通** ⭐
✅ ecommerce_etl DAG 部署 + 触发
✅ 解决 6 个真实问题:

| # | 问题 | 解决 |
|---|------|------|
| 1 | Airflow 不支持 Windows | 改用 Docker Desktop(官方推荐) |
| 2 | pip 装到 Python 3.13 不兼容 | 装 Airflow 2.11(支持 3.13) |
| 3 | 容器启动失败:LOAD_EXAMPLES=yes | 改成 LOAD_EXAMPLES=true(bool 严格) |
| 4 | 找不到密码(默认账号不是 admin/admin) | 从容器文件 `/opt/airflow/standalone_admin_password.txt` 读 |
| 5 | 容器内无 pymysql | 用 airflow 用户装 `pip install pymysql` |
| 6 | 容器内路径用 Windows 路径(F:\...) | 改用容器内路径(/workspace/...)+ docker cp 脚本到容器 |

---

## 数据亮点

### Docker Desktop 部署
- 引擎:WSL 2 backend
- 镜像:`apache/airflow:2.10.2-python3.11`
- 资源:4 CPU + 6 GB RAM
- 容器名:airflow

### hello_world DAG(完美跑通) ✅

3 个任务:
```
hello_task (PythonOperator) → date_task (BashOperator) → goodbye_task (PythonOperator)
```

- Status: success
- Duration: 23 秒
- User: airflow

### ecommerce_etl DAG(部署完成 + 触发 1 次)

4 个任务:
```
ods_to_dwd → dwd_to_dws → data_quality_check → send_notification
```

- Schedule: `0 2 * * *`(每天凌晨 2 点)
- 触发方式:manual
- 状态:第一次失败(脚本路径问题),已修复路径

---

## 关键学习

### 1. Airflow 在 Windows 上的限制
- **官方不支持 Windows 原生运行**(fcntl 模块不存在)
- 必须用 **Docker Desktop / WSL2 / Linux Containers**
- 这是学到的最重要的"跨平台"教训

### 2. 容器化思维
- 容器是独立的 Linux 环境,不是 Windows 延伸
- 路径用 `/workspace/...` 而不是 `F:\...`
- 包必须装在容器内(`docker exec ... pip install`)
- 配置文件改后**需要重启**或触发 DAG 重新加载

### 3. Airflow 2.10+ 关键差异
- `LOAD_EXAMPLES` 接受 `true`/`false`,**不接受** `yes`/`no`
- standalone 模式密码写到文件,不显示在日志
- DAG 在 `start_date` 之后才被 scheduler 检测

### 4. Debug 流程
1. 看 Docker Desktop 容器状态(STATUS 列)
2. `docker logs airflow | grep error`
3. 在 Airflow UI 点任务 → **Logs** 标签(不是 Event Log)
4. `docker exec -u root` 进入容器 debug

---

## 项目结构更新

```
07-airflow-dag/                      ← 新增
├── README.md                        # Airflow 入门文档
├── install_airflow.md               # 安装指南
├── dags/
│   ├── hello_world.py               # 第一个 DAG ✅
│   └── ecommerce_etl.py            # 电商 ETL DAG
├── plugins/
│   └── etl_functions.py            # ETL 函数库
└── logs/                            # Airflow 日志目录
```

---

## 简历故事(Week 5 部分)

> **Apache Airflow 自动化 ETL 编排** | [github.com/Three-rgb/ecommerce-data-warehouse](https://github.com/Three-rgb/ecommerce-data-warehouse)
>
> 部署 Apache Airflow 2.10.2 到 Docker,设计并实现了电商数仓的自动化 ETL 流程:
> - 使用 `PythonOperator` + `BashOperator` 编排 4 个任务(ODS→DWD→DWS→校验→通知)
> - 配置 `schedule_interval='0 2 * * *'` 实现每天凌晨 2 点自动跑
> - 解决了 6 个真实问题:Windows 兼容性、Python 版本兼容、Airflow 配置 strict 模式、容器内依赖管理、跨平台路径问题、Docker 资源分配
>
> **核心收获**:理解了"容器化部署"和"跨平台路径"的实际坑,学会了用 docker exec / docker logs / docker cp 排查容器内问题。

---

## 经验教训(Week 5 复盘)

### 1. 提前判断平台兼容性
- 在装 Airflow 前应该先查官方支持矩阵
- **Windows 不支持原生的 fcntl 模块**,要装 Docker
- 浪费了 30 分钟装 Python 3.11(结果 3.13 也可以)

### 2. 不要重复踩同一个坑
- 第一次 LOAD_EXAMPLES=yes 报错,**没意识到是值问题**
- 第二次重装 Python 还是装 Airflow
- **应该一开始看完整报错,而不是反复重试**

### 3. 容器操作要有"root 思维"
- 默认 airflow 用户权限有限
- 改文件需要 `-u root`
- 装包直接用 airflow 用户(`/home/airflow/.local/bin/pip`)

### 4. 跨平台路径是大坑
- 写代码时就要考虑:**这段代码是跑在 Linux 还是 Windows?**
- Airflow 容器是 Linux,要用 `/workspace/...`
- 真实生产:**配置文件用环境变量,不要硬编码路径**

### 5. PowerShell 的 quoting 陷阱
- `"` 在 PowerShell 里是字符串,但 `"` 内嵌套 `"` 需要转义
- `>` 是重定向符,会把命令输出重定向到文件
- **用单引号 `'...'` 更安全**(字面量字符串)
- 复杂命令建议**写到 .ps1 脚本里执行**

---

## 后续改进(下次专门搞)

1. **ecommerce_etl 真正跑通**
   - 把 etl_functions.py 重写,所有逻辑内联,不依赖外部文件
   - 用 Docker volume 挂载 F:\Projects,这样容器和 Windows 共享代码
   - 解决 standalone 模式重复启动的问题

2. **加告警**
   - 任务失败发邮件
   - 用 EmailOperator 配置 SMTP

3. **加监控**
   - 接入 Prometheus + Grafana
   - 监控任务执行时长、成功率

4. **生产级**
   - 切换到 docker-compose 部署(更稳定)
   - 用 PostgreSQL 替代 SQLite 存元数据
   - 用 Redis 做消息队列

---

## 项目时间线

```
Week 1 ✅ 造数据(100万订单)        1 day
Week 2 ✅ ODS 层(4张表入 MySQL)     1 day
Week 3 ✅ DWD 层(2张表 + 6道 SQL)   1 day
Week 4 ✅ DWS 层(3张宽表 + RFM)     1 day
Week 5 ✅ Airflow 调度(9 小时 debug)  1 day
```

**5 周完成数仓核心 4 层 + Airflow 自动化** — 这就是你的"数仓工程师"作品集。

---

## 接下来

**A. 写完 Week 5 收官 + commit**(今天的目标)
**B. 重启 ecommerce_etl 让它跑通**(可选,如果精力够)
**C. Week 6 准备**(K8s 部署 + Spark 入门)

---

**记录时间**:2026-06-18/19
**作者**:zhao
**Week 5 状态**:核心完成(hello_world 跑通 + 框架就位)
**待优化**:ecommerce_etl DAG 完整跑通
