"""
ODS 层 MySQL 验证脚本
跑几个查询,确认 ODS 数据质量
"""

import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from db_config import get_mysql_url, DATABASE_NAME  # noqa


def run_query(engine, sql, title):
    print("=" * 60)
    print(f"📊 {title}")
    print("=" * 60)
    df = pd.read_sql(text(sql), engine)
    print(df.to_string(index=False))
    print()
    return df


def main():
    print(f"✅ 连接 MySQL: {DATABASE_NAME}")
    engine = create_engine(get_mysql_url(DATABASE_NAME))
    print()

    # 1. 各表行数
    run_query(
        engine,
        """
        SELECT 'ods_users' AS table_name, COUNT(*) AS rows_count FROM ods_users
        UNION ALL SELECT 'ods_products', COUNT(*) FROM ods_products
        UNION ALL SELECT 'ods_orders', COUNT(*) FROM ods_orders
        UNION ALL SELECT 'ods_order_items', COUNT(*) FROM ods_order_items
        """,
        "1. ODS 各表行数",
    )

    # 2. 订单状态分布
    run_query(
        engine,
        """
        SELECT
            status,
            COUNT(*) AS cnt,
            ROUND(COUNT(*)*100/SUM(COUNT(*)) OVER(), 2) AS pct
        FROM ods_orders
        GROUP BY status
        ORDER BY cnt DESC
        """,
        "2. 订单状态分布",
    )

    # 3. 有效订单的金额统计
    run_query(
        engine,
        """
        SELECT
            COUNT(*) AS paid_orders,
            ROUND(SUM(total_amount), 2) AS gmv,
            ROUND(AVG(total_amount), 2) AS avg_order_value,
            ROUND(MIN(total_amount), 2) AS min_amt,
            ROUND(MAX(total_amount), 2) AS max_amt
        FROM ods_orders
        WHERE status IN ('paid', 'shipped', 'received')
        """,
        "3. 有效订单(已支付)金额统计",
    )

    # 4. 用户城市 Top 10
    run_query(
        engine,
        """
        SELECT city, COUNT(*) AS user_count
        FROM ods_users
        GROUP BY city
        ORDER BY user_count DESC
        LIMIT 10
        """,
        "4. 用户城市分布 Top 10",
    )

    # 5. 各品类 GMV
    run_query(
        engine,
        """
        SELECT
            p.category,
            COUNT(DISTINCT oi.order_id) AS order_count,
            ROUND(SUM(oi.amount), 2) AS gmv
        FROM ods_order_items oi
        JOIN ods_products p ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY gmv DESC
        """,
        "5. 各品类订单数和 GMV",
    )

    # 6. 数据质量
    run_query(
        engine,
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS null_user,
            SUM(CASE WHEN total_amount IS NULL THEN 1 ELSE 0 END) AS null_amount,
            SUM(CASE WHEN total_amount <= 0 THEN 1 ELSE 0 END) AS invalid_amount,
            SUM(CASE WHEN total_amount > 100000 THEN 1 ELSE 0 END) AS suspicious_amount
        FROM ods_orders
        """,
        "6. 数据质量检查",
    )

    # 7. 时间范围
    run_query(
        engine,
        """
        SELECT
            MIN(create_time) AS earliest,
            MAX(create_time) AS latest,
            DATEDIFF(MAX(create_time), MIN(create_time)) AS day_span
        FROM ods_orders
        """,
        "7. 订单时间范围",
    )

    engine.dispose()
    print("✅ MySQL 验证完成!")
    return 0


if __name__ == "__main__":
    exit(main())
