"""
数据质量检查脚本 — DockerOperator Task 3
检查 DWS 各表行数是否在预期范围内
"""
import os
import sys
from datetime import datetime

import pymysql

MYSQL = {
    "host": os.getenv("MYSQL_HOST", "host.docker.internal"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "123456"),
    "database": os.getenv("MYSQL_DATABASE", "ecommerce_dw"),
    "charset": "utf8mb4",
}


def main():
    print("=" * 60)
    print(f"[{datetime.now()}] Task 3: 数据质量检查")
    print("=" * 60)

    conn = pymysql.connect(**MYSQL)
    try:
        with conn.cursor() as cursor:
            checks = {
                "dws_user_summary": (90000, 110000),
                "dws_product_summary": (4500, 5500),
                "dws_date_summary": (300, 400),
            }

            all_passed = True
            for table, (min_rows, max_rows) in checks.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = "PASS" if min_rows <= count <= max_rows else "FAIL"
                print(f"  [{status}] {table}: {count} rows (expected {min_rows}-{max_rows})")
                if not (min_rows <= count <= max_rows):
                    all_passed = False

            if not all_passed:
                print("\n[FAIL] 数据质量检查失败!")
                sys.exit(1)
    finally:
        conn.close()

    print(f"\n[{datetime.now()}] 数据质量检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
