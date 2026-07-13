# ============================================================
# ETL 任务镜像 — DockerOperator 每次启一个临时容器跑
#
# 构建:
#   docker build -f docker/etl/Dockerfile -t ecommerce-etl:latest .
#
# 用法:
#   docker run --rm ecommerce-etl:latest python /app/load_to_dwd.py
#   docker run --rm ecommerce-etl:latest python /app/load_to_dws.py
#   docker run --rm ecommerce-etl:latest python /app/quality_check.py
#   docker run --rm ecommerce-etl:latest python /app/send_notification.py
# ============================================================
FROM python:3.11-slim

# 只装 ETL 需要的(不装 Faker/tqdm/SQLAlchemy 等用不到的)
RUN pip install --no-cache-dir \
    pymysql==1.1.1 \
    pandas==2.2.3

# ETL 脚本
COPY 03-dwd-layer/scripts/load_to_dwd.py   /app/load_to_dwd.py
COPY 04-dws-layer/scripts/load_to_dws.py   /app/load_to_dws.py

# Airflow 任务脚本
COPY 07-airflow-dag/scripts/quality_check.py    /app/quality_check.py
COPY 07-airflow-dag/scripts/send_notification.py /app/send_notification.py

# 入口
COPY docker/etl/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["echo", "ETL image ready. Usage: docker run ecommerce-etl python /app/load_to_dwd.py"]
