"""
DWS 层验证脚本
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

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
    print("✅ 连接 DWS 层")
    conn = pymysql.connect(**MYSQL)
    print()

    # 1. 各表行数
    run_query(
        conn,
        """
        SELECT 'dws_user_summary' AS table_name, COUNT(*) AS rows_count FROM dws_user_summary
        UNION ALL SELECT 'dws_product_summary', COUNT(*) FROM dws_product_summary
        UNION ALL SELECT 'dws_date_summary', COUNT(*) FROM dws_date_summary
        """,
        "1. DWS 各表行数",
    )

    # 2. RFM 客户分层分布 ⭐
    run_query(
        conn,
        """
        SELECT
            rfm_segment,
            COUNT(*) AS user_count,
            ROUND(AVG(total_amount), 2) AS avg_amount
        FROM dws_user_summary
        WHERE valid_orders > 0
        GROUP BY rfm_segment
        ORDER BY user_count DESC
        """,
        "2. 8 类客户分层(核心!)⭐",
    )

    # 3. RFM 分数分布
    run_query(
        conn,
        """
        SELECT
            rfm_score,
            COUNT(*) AS user_count
        FROM dws_user_summary
        WHERE valid_orders > 0
        GROUP BY rfm_score
        ORDER BY rfm_score DESC
        LIMIT 20
        """,
        "3. RFM 三位分数 Top 20",
    )

    # 4. 用户复购情况
    run_query(
        conn,
        """
        SELECT
            is_repurchase,
            COUNT(*) AS user_count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
        FROM dws_user_summary
        WHERE valid_orders > 0
        GROUP BY is_repurchase
        """,
        "4. 复购 vs 单次",
    )

    # 5. Top 10 累计消费用户
    run_query(
        conn,
        """
        SELECT
            user_id, username, city,
            valid_orders,
            ROUND(total_amount, 2) AS total_amount,
            rfm_segment
        FROM dws_user_summary
        WHERE valid_orders > 0
        ORDER BY total_amount DESC
        LIMIT 10
        """,
        "5. 累计消费 Top 10 用户",
    )

    # 6. 商品销售 Top 10
    run_query(
        conn,
        """
        SELECT
            product_id, product_name, category, brand,
            total_quantity, ROUND(total_amount, 2) AS total_amount,
            total_users, category_rank
        FROM dws_product_summary
        WHERE total_amount > 0
        ORDER BY total_amount DESC
        LIMIT 10
        """,
        "6. 商品销售 Top 10",
    )

    # 7. 时间宽表 - 月度汇总
    run_query(
        conn,
        """
        SELECT
            year, month,
            ROUND(AVG(dau), 0) AS avg_dau,
            SUM(valid_orders) AS total_orders,
            ROUND(SUM(total_amount), 2) AS monthly_gmv
        FROM dws_date_summary
        GROUP BY year, month
        ORDER BY year, month
        """,
        "7. 月度汇总",
    )

    conn.close()
    print("✅ DWS 验证完成")
    return 0


if __name__ == "__main__":
    exit(main())
