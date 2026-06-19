"""
ETL 函数库 - Airflow 任务用的
这些函数被 ecommerce_etl.py 调用
"""

import sys
import time
from datetime import datetime
from pathlib import Path


# MySQL 配置(内嵌,避免外部依赖)
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "ecommerce_dw",
    "charset": "utf8mb4",
}


def task_ods_to_dwd():
    """
    任务 1:ODS → DWD
    调用 03-dwd-layer 的 load_to_dwd.py
    """
    import pymysql
    import importlib.util

    print("=" * 60)
    print(f"[{datetime.now()}] 任务1: ODS → DWD 开始")
    print("=" * 60)

    # 动态加载 load_to_dwd 模块
    script_path = r"F:\Projects\ecommerce-data-warehouse\03-dwd-layer\scripts\load_to_dwd.py"
    spec = importlib.util.spec_from_file_location("load_to_dwd", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["load_to_dwd"] = module
    spec.loader.exec_module(module)

    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        # 跑 DWD 接入
        conn.cursor().execute("SELECT 1")  # 测试连接
        print("✓ ODS 数据源已就绪")

        # 调用模块里的函数
        module.build_dwd_orders(conn)
        module.build_dwd_order_items(conn)
    finally:
        conn.close()

    print(f"[{datetime.now()}] 任务1: ODS → DWD 完成")
    return "ODS to DWD done"


def task_dwd_to_dws():
    """
    任务 2:DWD → DWS
    调用 04-dws-layer 的 build_dws_user_summary 等
    """
    import pymysql
    import importlib.util

    print("=" * 60)
    print(f"[{datetime.now()}] 任务2: DWD → DWS 开始")
    print("=" * 60)

    # 动态加载 load_to_dws 模块
    script_path = r"F:\Projects\ecommerce-data-warehouse\04-dws-layer\scripts\load_to_dws.py"
    spec = importlib.util.spec_from_file_location("load_to_dws", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["load_to_dws"] = module
    spec.loader.exec_module(module)

    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        module.build_dws_user_summary(conn)
        module.build_dws_product_summary(conn)
        module.build_dws_date_summary(conn)
    finally:
        conn.close()

    print(f"[{datetime.now()}] 任务2: DWD → DWS 完成")
    return "DWD to DWS done"


def task_data_quality_check():
    """
    任务 3:数据质量检查
    检查 DWS 各表行数是否符合预期
    """
    import pymysql

    print("=" * 60)
    print(f"[{datetime.now()}] 任务3: 数据质量检查")
    print("=" * 60)

    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        with conn.cursor() as cursor:
            # 检查 DWS 各表行数
            checks = {
                'dws_user_summary': (90000, 110000),  # 期望 9-11 万
                'dws_product_summary': (4500, 5500),   # 期望 4500-5500
                'dws_date_summary': (300, 400),        # 期望 300-400 天
            }

            all_passed = True
            for table, (min_rows, max_rows) in checks.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                status = "✅" if min_rows <= count <= max_rows else "❌"
                print(f"  {status} {table}: {count} 行 (期望 {min_rows}-{max_rows})")
                if not (min_rows <= count <= max_rows):
                    all_passed = False

            if not all_passed:
                raise ValueError("数据质量检查失败!")
    finally:
        conn.close()

    print(f"[{datetime.now()}] 任务3: 数据质量检查通过 ✅")
    return "Data quality check passed"


def task_send_notification():
    """
    任务 4:发送通知(模拟)
    真实环境会用 EmailOperator / DingTalk Operator
    """
    print("=" * 60)
    print(f"[{datetime.now()}] 任务4: 发送完成通知")
    print("=" * 60)
    print("📧 [模拟] 邮件已发送给数据团队")
    print("   主题: 每日 ETL 完成")
    print("   内容: ODS→DWD→DWS 全部成功,数据已就绪")
    return "Notification sent"
