# ============================================================
# Airflow 自定义镜像 — 预装 docker provider
# DockerOperator 依赖 apache-airflow-providers-docker
# ============================================================
FROM apache/airflow:2.10.2-python3.11

USER airflow
RUN pip install --no-cache-dir apache-airflow-providers-docker==3.14.0
