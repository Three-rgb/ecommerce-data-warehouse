"""
DWD 层验证脚本
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent

# 直接定义 MySQL 配置
MYSQL = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "ecommerce_dw",
    "charset": "utf8mb4",
}


def run_query(conn, sql, title):
    print("=" * 60)
    print(f"📊 {title}")
    print("=" * 60)
    df = pd.read_sql(sql, conn)
    print(df.to_string(index=False))
    print()
    return df


def main():
    print("✅ 连接 DWD 层")
    conn = pymysql.connect(**MYSQL)
    print()

    # 1. 各表行数
    run_query(
        conn,
        """
        SELECT 'dwd_orders' AS table_name, COUNT(*) AS total,
               SUM(is_valid_order) AS valid_cnt,
               SUM(is_first_order) AS first_order_cnt
        FROM dwd_orders
        UNION ALL
        SELECT 'dwd_order_items', COUNT(*),
               SUM(is_valid_order), NULL
        FROM dwd_order_items
        """,
        "1. DWD 各表行数(带业务标记统计)",
    )

    # 2. 有效订单 vs 无效订单
    run_query(
        conn,
        """
        SELECT
            is_valid_order,
            COUNT(*) AS order_count,
            ROUND(SUM(total_amount), 2) AS total_amount
        FROM dwd_orders
        GROUP BY is_valid_order
        """,
        "2. 有效订单 vs 无效订单",
    )

    # 3. 首单用户特征
    run_query(
        conn,
        """
        SELECT
            city,
            COUNT(*) AS first_order_user_count,
            ROUND(AVG(total_amount), 2) AS avg_first_order_amount
        FROM dwd_orders
        WHERE is_first_order = 1 AND is_valid_order = 1
        GROUP BY city
        ORDER BY first_order_user_count DESC
        LIMIT 10
        """,
        "3. 首单用户城市分布 Top 10",
    )

    # 4. 各品类 GMV(从 dwd_order_items 直接查,不用 JOIN)
    run_query(
        conn,
        """
        SELECT
            category,
            COUNT(DISTINCT order_id) AS order_count,
            ROUND(SUM(amount), 2) AS gmv
        FROM dwd_order_items
        WHERE is_valid_order = 1
        GROUP BY category
        ORDER BY gmv DESC
        """,
        "4. 各品类 GMV(已退化,无需 JOIN)",
    )

    # 5. 订单时间分布
    run_query(
        conn,
        """
        SELECT
            order_hour,
            COUNT(*) AS order_count
        FROM dwd_orders
        WHERE is_valid_order = 1
        GROUP BY order_hour
        ORDER BY order_hour
        """,
        "5. 有效订单的下单小时分布",
    )

    # 6. 用户等级 vs 消费
    run_query(
        conn,
        """
        SELECT
            user_level,
            COUNT(DISTINCT user_id) AS user_count,
            ROUND(AVG(total_amount), 2) AS avg_order_amount
        FROM dwd_orders
        WHERE is_valid_order = 1
        GROUP BY user_level
        ORDER BY user_level
        """,
        "6. 用户等级与消费水平",
    )

    # 7. 维度退化效果对比(用 dwd 直接查 vs JOIN 查,看速度)
    print("=" * 60)
    print("📊 7. 维度退化效果:直接查 dwd vs JOIN 查 ods")
    print("=" * 60)
    import time
    t0 = time.time()
    df1 = pd.read_sql(
        "SELECT order_id, username, total_amount FROM dwd_orders LIMIT 100000",
        conn,
    )
    t1 = time.time() - t0
    print(f"  dwd_orders 直接查: {t1*1000:.0f} ms ({len(df1)} 行)")

    t0 = time.time()
    df2 = pd.read_sql(
        """
        SELECT o.order_id, u.username, o.total_amount
        FROM ods_orders o
        LEFT JOIN ods_users u ON o.user_id = u.user_id
        LIMIT 100000
        """,
        conn,
    )
    t2 = time.time() - t0
    print(f"  JOIN ods 查询:    {t2*1000:.0f} ms ({len(df2)} 行)")
    print(f"  维度退化提速: {(t2-t1)*1000:.0f} ms ({(t2/t1):.1f}x)")

    conn.close()
    print()
    print("✅ DWD 验证完成")
    return 0


if __name__ == "__main__":
    exit(main())
