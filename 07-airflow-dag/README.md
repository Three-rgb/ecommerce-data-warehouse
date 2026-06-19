# Week 5 - Airflow 调度编排

## 什么是 Airflow?

Apache Airflow 是 Airbnb 开源的**工作流调度平台**,核心能力:
- 把多个任务编排成 DAG(有向无环图)
- 按时间/依赖自动执行
- 监控任务状态(成功/失败/重试)
- 失败告警(邮件/钉钉/Slack)

## 核心概念

### DAG(有向无环图)
```
[task1: 抽数据] → [task2: 清洗] → [task3: 聚合] → [task4: 通知]
        ↓
   失败重试
```

### Operator(任务类型)
- `PythonOperator` - 跑 Python 函数
- `BashOperator` - 跑 shell 命令
- `MySqlOperator` - 跑 SQL
- `EmailOperator` - 发邮件
- 几十种

### Schedule(调度规则)
- `schedule_interval='0 2 * * *'` - 每天凌晨 2 点
- `schedule_interval='@hourly'` - 每小时
- `schedule_interval=timedelta(minutes=30)` - 每 30 分钟

## 文件结构

```
07-airflow-dag/
├── README.md                  # 本文档
├── install_airflow.md         # 安装指南
├── dags/
│   ├── hello_world.py         # 第一个 DAG
│   └── ecommerce_etl.py       # 电商 ETL DAG
├── plugins/
│   └── etl_functions.py       # ETL 函数库
└── logs/                      # Airflow 日志目录
```

## 学习路径

1. **装 Airflow**(30 分钟)
2. **跑 hello_world.py**(15 分钟,看 DAG 在 Web UI 长啥样)
3. **改造之前的 ETL 脚本为 Airflow 任务**(60 分钟)
4. **设置调度规则**(每天凌晨 2 点)
5. **配置告警**(任务失败发邮件)

## 真实工作场景

```
每天凌晨 2 点,Airflow 自动:
1. 从 MySQL 抽数据到 ODS
2. 清洗数据到 DWD
3. 聚合到 DWS
4. 计算业务指标(ADS)
5. 数据质量检查
6. 失败 → 发邮件给数据团队
7. 成功 → 发钉钉通知
```

## 为什么 Airflow 重要?

1. **简历加分** - "用 Airflow 编排 ETL" 真实工作里 100% 会用
2. **自动化** - 不用每天手动跑脚本
3. **可观测** - 任务状态、时间、失败原因一目了然
4. **重试机制** - 任务失败自动重试,不用盯着
5. **依赖管理** - 任务按依赖顺序跑,不会乱序

## 启动

详见 `install_airflow.md`。
