"""
电商数仓 ETL DAG — DockerOperator 版
每个 Task 启一个独立临时容器,跑完即删

DAG 结构:
  [ods_to_dwd] → [dwd_to_dws] → [data_quality_check] → [send_notification]

触发方式:
  - 定时:每天凌晨 2 点(@daily)
  - Web UI:手动 Trigger DAG
  - CLI: airflow dags trigger ecommerce_etl_docker
"""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.email import EmailOperator
from airflow.providers.docker.operators.docker import DockerOperator

# ============================================================
# 配置
# ============================================================

# MySQL 连接信息 → 注入每个 Task 容器的环境变量
MYSQL_ENV = {
    "MYSQL_HOST": "host.docker.internal",
    "MYSQL_PORT": "3306",
    "MYSQL_USER": "root",
    "MYSQL_PASSWORD": "123456",
    "MYSQL_DATABASE": "ecommerce_dw",
}

# ETL 任务镜像
ETL_IMAGE = "ecommerce-etl:latest"

# Docker socket
DOCKER_URL = "unix://var/run/docker.sock"

# ============================================================
# DAG 定义
# ============================================================

# 收件邮箱
ALERT_EMAIL = "3075758453@qq.com"

default_args = {
    "owner": "zhao",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "email": [ALERT_EMAIL],          # 告警收件人
    "email_on_failure": True,        # 失败自动发邮件
    "email_on_retry": True,          # 重试也通知
    "execution_timeout": timedelta(hours=2),
}

with DAG(
    dag_id="ecommerce_etl_docker",
    default_args=default_args,
    description="电商数仓每日 ETL — DockerOperator 隔离执行",
    schedule_interval="0 2 * * *",  # 每天凌晨 2 点
    catchup=False,
    max_active_runs=1,  # 防止并发跑同一条管道(TRUNCATE + INSERT 不能并行)
    tags=["etl", "data-warehouse", "ecommerce", "docker-operator"],
) as dag:

    # ---- Task 1: ODS → DWD ----
    t_ods_to_dwd = DockerOperator(
        task_id="ods_to_dwd",
        image=ETL_IMAGE,
        command="python /app/load_to_dwd.py",
        docker_url=DOCKER_URL,
        network_mode="bridge",
        auto_remove=False,  # 让 Airflow 自己清理，避免和 Docker daemon 冲突
        environment=MYSQL_ENV,
        api_version="auto",
        execution_timeout=timedelta(hours=1),
    )

    # ---- Task 2: DWD → DWS ----
    t_dwd_to_dws = DockerOperator(
        task_id="dwd_to_dws",
        image=ETL_IMAGE,
        command="python /app/load_to_dws.py",
        docker_url=DOCKER_URL,
        network_mode="bridge",
        auto_remove=False,  # 让 Airflow 自己清理，避免和 Docker daemon 冲突
        environment=MYSQL_ENV,
        api_version="auto",
        execution_timeout=timedelta(hours=1),
    )

    # ---- Task 3: 数据质量检查 ----
    t_quality = DockerOperator(
        task_id="data_quality_check",
        image=ETL_IMAGE,
        command="python /app/quality_check.py",
        docker_url=DOCKER_URL,
        network_mode="bridge",
        auto_remove=False,  # 让 Airflow 自己清理，避免和 Docker daemon 冲突
        environment=MYSQL_ENV,
        api_version="auto",
    )

    # ---- Task 4: 成功通知邮件 ----
    t_notify = EmailOperator(
        task_id="send_notification",
        to=[ALERT_EMAIL],
        subject="[电商数仓] 每日 ETL 完成 ✅",
        html_content="""
        <h3>电商数仓每日 ETL 执行成功</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr><td><b>DAG</b></td><td>ecommerce_etl_docker</td></tr>
            <tr><td><b>执行时间</b></td><td>{{ execution_date }}</td></tr>
            <tr><td><b>任务链</b></td><td>ODS → DWD → DWS → 质量检查 ✅</td></tr>
            <tr><td><b>数据规模</b></td><td>100 万订单 / 320 万明细</td></tr>
        </table>
        <p>数据已就绪，可以开始分析。</p>
        """,
    )

    # 依赖关系:顺序执行
    t_ods_to_dwd >> t_dwd_to_dws >> t_quality >> t_notify
