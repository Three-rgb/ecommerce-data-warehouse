"""
只跑 dws_date_summary(避免重跑全部)
适用:dws_user_summary 和 dws_product_summary 已经建好,只需要补 dws_date_summary
"""

import time
from pathlib import Path

import pymysql

MYSQL = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "ecommerce_dw",
    "charset": "utf8mb4",
}

# 只建 dws_date_summary 表(如果不存在)
DDL = """
CREATE TABLE IF NOT EXISTS dws_date_summary (
    date               DATE NOT NULL,
    dau                INT,
    new_users          INT,
    repurchase_users   INT,
    total_active_users INT,
    total_orders       INT,
    valid_orders       INT,
    total_amount       DECIMAL(15, 2),
    avg_order_value    DECIMAL(10, 2),
    avg_user_amount    DECIMAL(10, 2),
    year               INT,
    month              INT,
    weekday            INT,
    PRIMARY KEY (date),
    KEY idx_year_month (year, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 时间宽表';
"""


def main():
    print("=" * 60)
    print("只跑 dws_date_summary")
    print("=" * 60)
    print()

    conn = pymysql.connect(**MYSQL)
    cursor = conn.cursor()

    # 1. 建表
    print("[1] 创建 dws_date_summary 表(如果不存在)...")
    cursor.execute(DDL)
    conn.commit()
    print("    ✓ 表就绪")
    print()

    # 2. 清空
    print("[2] TRUNCATE dws_date_summary...")
    cursor.execute("TRUNCATE TABLE dws_date_summary")
    conn.commit()
    print("    ✓ 清空")
    print()

    # 3. 插入(用子查询避免 only_full_group_by)
    print("[3] 构建时间宽表...")
    t0 = time.time()

    insert_sql = """
    INSERT INTO dws_date_summary (
        date, dau, new_users, repurchase_users, total_active_users,
        total_orders, valid_orders, total_amount, avg_order_value, avg_user_amount,
        year, month, weekday
    )
    SELECT
        date,
        dau, new_users, repurchase_users, total_active_users,
        total_orders, valid_orders, total_amount, avg_order_value, avg_user_amount,
        YEAR(date) AS year,
        MONTH(date) AS month,
        WEEKDAY(date) + 1 AS weekday
    FROM (
        SELECT
            DATE(o.create_time) AS date,
            COUNT(DISTINCT CASE WHEN o.is_valid_order = 1 THEN o.user_id END) AS dau,
            COUNT(DISTINCT CASE WHEN o.is_first_order = 1 AND o.is_valid_order = 1 THEN o.user_id END) AS new_users,
            COUNT(DISTINCT CASE WHEN o.is_valid_order = 1 AND u_summary.is_repurchase = 1 THEN o.user_id END) AS repurchase_users,
            COUNT(DISTINCT o.user_id) AS total_active_users,
            COUNT(DISTINCT o.order_id) AS total_orders,
            SUM(CASE WHEN o.is_valid_order = 1 THEN 1 ELSE 0 END) AS valid_orders,
            ROUND(SUM(CASE WHEN o.is_valid_order = 1 THEN o.total_amount ELSE 0 END), 2) AS total_amount,
            ROUND(AVG(CASE WHEN o.is_valid_order = 1 THEN o.total_amount END), 2) AS avg_order_value,
            ROUND(SUM(CASE WHEN o.is_valid_order = 1 THEN o.total_amount ELSE 0 END) / NULLIF(COUNT(DISTINCT CASE WHEN o.is_valid_order = 1 THEN o.user_id END), 0), 2) AS avg_user_amount
        FROM dwd_orders o
        LEFT JOIN dws_user_summary u_summary ON o.user_id = u_summary.user_id
        GROUP BY DATE(o.create_time)
    ) t
    """
    cursor.execute(insert_sql)
    conn.commit()
    print(f"    ✓ 耗时 {time.time()-t0:.1f}s")
    print()

    # 4. 验证
    cursor.execute("SELECT COUNT(*), SUM(dau), SUM(total_amount) FROM dws_date_summary")
    days, total_dau, total_amount = cursor.fetchone()
    print(f"  ✅ 完成!天数: {days}, 总 DAU: {total_dau or 0:,}, 总 GMV: {total_amount or 0:,.0f} 元")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
