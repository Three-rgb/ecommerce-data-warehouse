"""
ODS 层验证脚本
跑几个查询,确认 ODS 数据质量
"""

from pathlib import Path

import duckdb
import pandas as pd

ODS_DIR = Path(__file__).parent.parent
DUCKDB_FILE = ODS_DIR / "ods.duckdb"


def run_query(con, sql, title):
    print("=" * 60)
    print(f"📊 {title}")
    print("=" * 60)
    df = con.execute(sql).df()
    print(df.to_string(index=False))
    print()
    return df


def main():
    if not DUCKDB_FILE.exists():
        print(f"[错误] 找不到 {DUCKDB_FILE}")
        print("       请先跑 load_to_duckdb.py")
        return 1

    con = duckdb.connect(str(DUCKDB_FILE), read_only=True)

    print("✅ 连接 ODS DuckDB")
    print()

    # 各表行数
    run_query(
        con,
        """
        SELECT 'ods_users' AS table_name, COUNT(*) AS rows FROM ods_users
        UNION ALL SELECT 'ods_products', COUNT(*) FROM ods_products
        UNION ALL SELECT 'ods_orders', COUNT(*) FROM ods_orders
        UNION ALL SELECT 'ods_order_items', COUNT(*) FROM ods_order_items
        """,
        "1. ODS 各表行数",
    )

    # 订单状态分布
    run_query(
        con,
        """
        SELECT
            status,
            COUNT(*) AS cnt,
            ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 2) AS pct
        FROM ods_orders
        GROUP BY status
        ORDER BY cnt DESC
        """,
        "2. 订单状态分布",
    )

    # 有效订单(已支付)的客单价
    run_query(
        con,
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
        "3. 有效订单的金额统计",
    )

    # 用户城市分布
    run_query(
        con,
        """
        SELECT city, COUNT(*) AS user_count
        FROM ods_users
        GROUP BY city
        ORDER BY user_count DESC
        LIMIT 10
        """,
        "4. 用户城市分布 Top 10",
    )

    # 各品类 GMV
    run_query(
        con,
        """
        SELECT
            p.category,
            COUNT(DISTINCT oi.order_id) AS order_cnt,
            ROUND(SUM(oi.amount), 2) AS gmv
        FROM ods_order_items oi
        JOIN ods_products p ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY gmv DESC
        """,
        "5. 各品类订单数和 GMV",
    )

    # 数据质量检查
    run_query(
        con,
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE user_id IS NULL) AS null_user,
            COUNT(*) FILTER (WHERE total_amount IS NULL) AS null_amount,
            COUNT(*) FILTER (WHERE total_amount <= 0) AS invalid_amount,
            COUNT(*) FILTER (WHERE total_amount > 100000) AS suspicious_amount
        FROM ods_orders
        """,
        "6. 数据质量检查",
    )

    con.close()
    print("✅ 验证完成")
    return 0


if __name__ == "__main__":
    exit(main())
