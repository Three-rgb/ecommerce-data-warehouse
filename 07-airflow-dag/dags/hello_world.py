"""
第一个 Airflow DAG - Hello World
作用:理解 DAG 基本结构

DAG 结构:
  hello_task → goodbye_task
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


def hello():
    """第一个任务:打印 Hello"""
    print("🎉 Hello, Airflow!")
    print(f"当前时间: {datetime.now()}")
    return "Hello done"


def goodbye():
    """第三个任务:打印 Goodbye"""
    print("👋 Goodbye, Airflow!")
    return "Goodbye done"


# 默认参数
default_args = {
    'owner': 'zhao',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 定义 DAG
with DAG(
    dag_id='hello_world',
    default_args=default_args,
    description='我的第一个 Airflow DAG',
    schedule_interval=timedelta(days=1),  # 每天跑一次
    catchup=False,  # 不补跑历史
    tags=['tutorial', 'beginner'],
) as dag:

    # 任务 1:Python 函数
    task1 = PythonOperator(
        task_id='hello_task',
        python_callable=hello,
    )

    # 任务 2:Bash 命令
    task2 = BashOperator(
        task_id='date_task',
        bash_command='echo "今天是 $(date)"',
    )

    # 任务 3:Python 函数
    task3 = PythonOperator(
        task_id='goodbye_task',
        python_callable=goodbye,
    )

    # 定义依赖关系:task1 → task2 → task3
    task1 >> task2 >> task3
