FROM apache/airflow:2.10.2-python3.11

# 直接以 airflow 用户装(不切到 root)
USER airflow
RUN pip install pymysql