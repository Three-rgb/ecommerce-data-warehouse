#!/bin/bash
# ============================================================
# ETL 镜像入口 — 双模式
#
# Airflow Task 模式(有参数):
#   docker run ecommerce-etl python /app/load_to_dwd.py
#   → exec 传入的命令
#
# 默认模式(无参数):
#   docker run ecommerce-etl
#   → 显示帮助信息
# ============================================================
set -e

if [ $# -gt 0 ]; then
    echo "=== ETL Task: $* ==="
    exec "$@"
else
    echo "============================================"
    echo "  E-Commerce ETL Task Image"
    echo "============================================"
    echo ""
    echo "Available commands:"
    echo "  python /app/load_to_dwd.py       — ODS → DWD"
    echo "  python /app/load_to_dws.py       — DWD → DWS"
    echo "  python /app/quality_check.py     — 数据质量检查"
    echo "  python /app/send_notification.py — 发送通知"
    echo ""
    echo "Env vars:"
    echo "  MYSQL_HOST     — default: host.docker.internal"
    echo "  MYSQL_PORT     — default: 3306"
    echo "  MYSQL_USER     — default: root"
    echo "  MYSQL_PASSWORD — default: 123456"
    echo "  MYSQL_DATABASE — default: ecommerce_dw"
    exit 0
fi
