"""
电商数仓 ETL DAG
作用:把 ODS → DWD → DWS → 数据质量检查 → 通知 全部自动化

调度:每天凌晨 2 点跑

DAG 结构:
  [ods_to_dwd] → [dwd_to_dws] → [data_quality_check] → [send_notification]
                       ↓ 失败
                   [alert_on_failure]
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

# 添加 plugins 路径,让 Airflow 能找到 etl_functions
sys.path.insert(0, str(Path(__file__).parent.parent / "plugins"))

from etl_functions import (
    task_ods_to_dwd,
    task_dwd_to_dws,
    task_data_quality_check,
    task_send_notification,
)


# 默认参数
default_args = {
    'owner': 'zhao',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': False,  # 真用邮件时改 True
    'execution_timeout': timedelta(hours=2),
}


with DAG(
    dag_id='ecommerce_etl',
    default_args=default_args,
    description='电商数仓每日 ETL',
    schedule_interval='0 2 * * *',  # 每天凌晨 2 点(Cron 表达式)
    catchup=False,
    tags=['etl', 'data-warehouse', 'ecommerce'],
) as dag:

    # 任务 1:ODS → DWD
    t_ods_to_dwd = PythonOperator(
        task_id='ods_to_dwd',
        python_callable=task_ods_to_dwd,
        execution_timeout=timedelta(hours=1),
    )

    # 任务 2:DWD → DWS
    t_dwd_to_dws = PythonOperator(
        task_id='dwd_to_dws',
        python_callable=task_dwd_to_dws,
        execution_timeout=timedelta(hours=1),
    )

    # 任务 3:数据质量检查
    t_quality = PythonOperator(
        task_id='data_quality_check',
        python_callable=task_data_quality_check,
    )

    # 任务 4:发送通知
    t_notify = PythonOperator(
        task_id='send_notification',
        python_callable=task_send_notification,
    )

    # 定义依赖关系(顺序执行)
    t_ods_to_dwd >> t_dwd_to_dws >> t_quality >> t_notify
