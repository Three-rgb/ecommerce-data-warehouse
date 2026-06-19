"""
DWS 层数据接入脚本
从 DWD 层构建用户/商品/时间宽表
"""

import sys
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

SCRIPT_DIR = Path(__file__).parent


DDL_DWS_USER = """
DROP TABLE IF EXISTS dws_user_summary;
CREATE TABLE dws_user_summary (
    user_id            VARCHAR(20) NOT NULL,
    username           VARCHAR(100),
    city               VARCHAR(50),
    user_level         VARCHAR(20),
    total_orders       INT,
    valid_orders       INT,
    total_quantity     INT,
    total_amount       DECIMAL(15, 2),
    first_order_date   DATE,
    last_order_date    DATE,
    days_since_last    INT,
    active_days        INT,
    avg_order_amount   DECIMAL(10, 2),
    avg_days_between   DECIMAL(10, 2),
    r_score            TINYINT,
    f_score            TINYINT,
    m_score            TINYINT,
    rfm_score          VARCHAR(10),
    rfm_segment        VARCHAR(50),
    favorite_category  VARCHAR(50),
    favorite_category_amount DECIMAL(15, 2),
    is_repurchase      TINYINT,
    PRIMARY KEY (user_id),
    KEY idx_rfm_segment (rfm_segment),
    KEY idx_r_score (r_score),
    KEY idx_m_score (m_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 用户宽表';
"""

DDL_DWS_PRODUCT = """
DROP TABLE IF EXISTS dws_product_summary;
CREATE TABLE dws_product_summary (
    product_id         VARCHAR(20) NOT NULL,
    product_name       VARCHAR(255),
    category           VARCHAR(50),
    sub_category       VARCHAR(50),
    brand              VARCHAR(100),
    price              DECIMAL(10, 2),
    total_quantity     INT,
    total_orders       INT,
    total_users        INT,
    total_amount       DECIMAL(15, 2),
    first_sale_date    DATE,
    last_sale_date     DATE,
    avg_quantity_per_order DECIMAL(10, 2),
    avg_user_quantity  DECIMAL(10, 2),
    category_rank      INT,
    PRIMARY KEY (product_id),
    KEY idx_category (category),
    KEY idx_brand (brand),
    KEY idx_total_amount (total_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 商品宽表';
"""

DDL_DWS_DATE = """
DROP TABLE IF EXISTS dws_date_summary;
CREATE TABLE dws_date_summary (
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


def execute_sql(conn, sql, name=""):
    if name:
        print(f"  -> {name}")
    cursor = conn.cursor()
    for stmt in sql.split(";"):
        s = stmt.strip()
        if s:
            cursor.execute(s)
    conn.commit()
    cursor.close()


def build_dws_user_summary(conn):
    print("\n[1/3] dws_user_summary...")
    t0 = time.time()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE dws_user_summary")

    cursor.execute("""
    INSERT INTO dws_user_summary (
        user_id, username, city, user_level,
        total_orders, valid_orders, total_quantity, total_amount,
        first_order_date, last_order_date, days_since_last, active_days,
        avg_order_amount, avg_days_between,
        is_repurchase,
        favorite_category, favorite_category_amount
    )
    SELECT
        u.user_id, u.username, u.city, u.level,
        COUNT(DISTINCT o.order_id),
        SUM(CASE WHEN o.is_valid_order = 1 THEN 1 ELSE 0 END),
        COALESCE(SUM(oi.quantity), 0),
        ROUND(SUM(CASE WHEN o.is_valid_order = 1 THEN o.total_amount ELSE 0 END), 2),
        MIN(DATE(o.create_time)),
        MAX(DATE(o.create_time)),
        DATEDIFF(CURDATE(), MAX(DATE(o.create_time))),
        COUNT(DISTINCT DATE(o.create_time)),
        ROUND(AVG(CASE WHEN o.is_valid_order = 1 THEN o.total_amount END), 2),
        CASE
            WHEN COUNT(DISTINCT DATE(o.create_time)) > 1
            THEN ROUND(DATEDIFF(MAX(DATE(o.create_time)), MIN(DATE(o.create_time))) * 1.0 / (COUNT(DISTINCT DATE(o.create_time)) - 1), 2)
            ELSE 0
        END,
        CASE WHEN COUNT(DISTINCT o.order_id) >= 2 THEN 1 ELSE 0 END,
        NULL, NULL
    FROM dwd_orders o
    RIGHT JOIN ods_users u ON o.user_id = u.user_id
    LEFT JOIN dwd_order_items oi ON o.order_id = oi.order_id AND o.is_valid_order = 1
    GROUP BY u.user_id, u.username, u.city, u.level
    """)
    conn.commit()
    print(f"  step 1 ok ({time.time()-t0:.1f}s)")

    cursor.execute("""
    UPDATE dws_user_summary u
    INNER JOIN (
        SELECT user_id,
               NTILE(5) OVER (ORDER BY days_since_last DESC) AS r_score,
               NTILE(5) OVER (ORDER BY valid_orders) AS f_score,
               NTILE(5) OVER (ORDER BY total_amount) AS m_score
        FROM dws_user_summary
        WHERE valid_orders > 0
    ) r ON u.user_id = r.user_id
    SET u.r_score = r.r_score, u.f_score = r.f_score, u.m_score = r.m_score
    """)
    conn.commit()

    cursor.execute("""
    UPDATE dws_user_summary
    SET rfm_score = CONCAT(r_score, f_score, m_score),
        rfm_segment = CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'A_Important_Value'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score >= 4 THEN 'B_Important_Develop'
            WHEN r_score >= 4 AND f_score <= 2 AND m_score >= 4 THEN 'C_Important_Keep'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 4 THEN 'D_Important_Recover'
            WHEN r_score >= 4 AND f_score >= 4 AND m_score <= 2 THEN 'E_General_Value'
            WHEN r_score <= 2 AND f_score >= 4 AND m_score <= 2 THEN 'F_General_Develop'
            WHEN r_score >= 4 AND f_score <= 2 AND m_score <= 2 THEN 'G_General_Keep'
            ELSE 'H_Churned'
        END
    """)
    conn.commit()

    cursor.execute("""
    UPDATE dws_user_summary u
    INNER JOIN (
        SELECT user_id, category,
               ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY SUM(amount) DESC) AS rn,
               SUM(amount) AS cat_amount
        FROM dwd_order_items
        WHERE is_valid_order = 1
        GROUP BY user_id, category
    ) f ON u.user_id = f.user_id AND f.rn = 1
    SET u.favorite_category = f.category,
        u.favorite_category_amount = f.cat_amount
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*), SUM(is_repurchase), COUNT(DISTINCT rfm_segment) FROM dws_user_summary")
    total, repurchase, segments = cursor.fetchone()
    print(f"  done: {total} users, {repurchase} repurchase, {segments} segments")
    cursor.close()


def build_dws_product_summary(conn):
    print("\n[2/3] dws_product_summary...")
    t0 = time.time()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE dws_product_summary")

    cursor.execute("""
    INSERT INTO dws_product_summary (
        product_id, product_name, category, sub_category, brand, price,
        total_quantity, total_orders, total_users, total_amount,
        first_sale_date, last_sale_date,
        avg_quantity_per_order, avg_user_quantity
    )
    SELECT
        oi.product_id,
        ANY_VALUE(oi.product_name),
        ANY_VALUE(oi.category),
        ANY_VALUE(oi.sub_category),
        ANY_VALUE(oi.brand),
        ANY_VALUE(oi.unit_price),
        SUM(oi.quantity),
        COUNT(DISTINCT oi.order_id),
        COUNT(DISTINCT oi.user_id),
        ROUND(SUM(oi.amount), 2),
        MIN(DATE(oi.order_time)),
        MAX(DATE(oi.order_time)),
        ROUND(AVG(oi.quantity), 2),
        ROUND(SUM(oi.quantity) * 1.0 / NULLIF(COUNT(DISTINCT oi.user_id), 0), 2)
    FROM dwd_order_items oi
    WHERE oi.is_valid_order = 1
    GROUP BY oi.product_id
    """)
    conn.commit()

    cursor.execute("""
    UPDATE dws_product_summary p
    INNER JOIN (
        SELECT product_id,
               RANK() OVER (PARTITION BY category ORDER BY total_quantity DESC) AS rnk
        FROM dws_product_summary
    ) r ON p.product_id = r.product_id
    SET p.category_rank = r.rnk
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*), SUM(total_amount) FROM dws_product_summary")
    total, amount = cursor.fetchone()
    print(f"  done: {total} products, {amount} GMV")
    cursor.close()


def build_dws_date_summary(conn):
    """
    构建时间宽表(修复版)
    用子查询避免 MySQL 8.0 only_full_group_by 错误
    """
    print("\n[3/3] dws_date_summary...")
    t0 = time.time()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE dws_date_summary")

    cursor.execute("""
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
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*), SUM(dau), SUM(total_amount) FROM dws_date_summary")
    days, total_dau, total_amount = cursor.fetchone()
    print(f"  done: {days} days, {total_dau} DAU, {total_amount} GMV")
    cursor.close()


def main():
    print("=" * 60)
    print("DWS Layer ETL")
    print("=" * 60)
    print()

    conn = pymysql.connect(**MYSQL)

    print("[0] Creating DWS tables...")
    execute_sql(conn, DDL_DWS_USER, "dws_user_summary")
    execute_sql(conn, DDL_DWS_PRODUCT, "dws_product_summary")
    execute_sql(conn, DDL_DWS_DATE, "dws_date_summary")
    print("    ok\n")

    build_dws_user_summary(conn)
    build_dws_product_summary(conn)
    build_dws_date_summary(conn)

    conn.close()
    print()
    print("=" * 60)
    print("DWS Layer Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()