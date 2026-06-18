"""
DWD 层数据接入脚本
作用:从 ODS 层读取,清洗 + 维度退化,写入 DWD 层

数据流:
  ods_orders + ods_users
    ↓ JOIN 维度退化
  dwd_orders
    ↓
    is_valid_order / is_first_order 业务标记

  ods_order_items + ods_products + dwd_orders
    ↓ JOIN 维度退化
  dwd_order_items
"""

import sys
import time
from pathlib import Path

import pymysql

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent

# 直接定义 MySQL 配置,不依赖外部文件
MYSQL = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "ecommerce_dw",
    "charset": "utf8mb4",
}


def execute_sql(conn, sql: str, name: str = ""):
    """执行一条/多条 SQL"""
    if name:
        print(f"  → 执行 {name}")
    cursor = conn.cursor()
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            cursor.execute(stmt)
    conn.commit()
    cursor.close()


# DDL 内嵌,不依赖外部文件
DDL_DWD_ORDERS = """
DROP TABLE IF EXISTS dwd_orders;
CREATE TABLE dwd_orders (
    order_id         VARCHAR(20) NOT NULL,
    user_id          VARCHAR(20),
    username         VARCHAR(100),
    age              INT,
    city             VARCHAR(50),
    user_level       VARCHAR(20),
    total_amount     DECIMAL(12, 2),
    item_count       INT,
    status           VARCHAR(20),
    create_time      DATETIME,
    pay_time         DATETIME,
    order_date       DATE,
    order_hour       INT,
    order_weekday    INT,
    is_valid_order   TINYINT(1) DEFAULT 0,
    is_first_order   TINYINT(1) DEFAULT 0,
    pay_latency_min  INT,
    PRIMARY KEY (order_id),
    KEY idx_user_id (user_id),
    KEY idx_create_time (create_time),
    KEY idx_order_date (order_date),
    KEY idx_user_date (user_id, order_date),
    KEY idx_valid_date (is_valid_order, order_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 订单事实表';
"""

DDL_DWD_ORDER_ITEMS = """
DROP TABLE IF EXISTS dwd_order_items;
CREATE TABLE dwd_order_items (
    order_id         VARCHAR(20) NOT NULL,
    product_id       VARCHAR(20) NOT NULL,
    quantity         INT,
    unit_price       DECIMAL(10, 2),
    amount           DECIMAL(12, 2),
    product_name     VARCHAR(255),
    category         VARCHAR(50),
    sub_category     VARCHAR(50),
    brand            VARCHAR(100),
    user_id          VARCHAR(20),
    order_time       DATETIME,
    is_valid_order   TINYINT(1),
    PRIMARY KEY (order_id, product_id),
    KEY idx_product_id (product_id),
    KEY idx_user_id (user_id),
    KEY idx_category (category),
    KEY idx_brand (brand),
    KEY idx_order_time (order_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD 订单明细事实表';
"""


def build_dwd_orders(conn):
    """
    从 ODS 构建 DWD 订单事实表
    包含:
      - 用户维度退化(username, age, city, level)
      - 时间分桶(order_date, order_hour, order_weekday)
      - 业务标记(is_valid_order, is_first_order, pay_latency_min)
    """
    print("\n[1/2] 构建 dwd_orders...")
    t0 = time.time()

    cursor = conn.cursor()

    # 1. 清空
    cursor.execute("TRUNCATE TABLE dwd_orders")

    # 2. 插入数据(JOIN + 业务标记)
    insert_sql = """
    INSERT INTO dwd_orders (
        order_id, user_id, username, age, city, user_level,
        total_amount, item_count, status,
        create_time, pay_time, order_date, order_hour, order_weekday,
        is_valid_order, is_first_order, pay_latency_min
    )
    SELECT
        o.order_id,
        o.user_id,
        u.username,
        u.age,
        u.city,
        u.level AS user_level,
        o.total_amount,
        o.item_count,
        o.status,
        o.create_time,
        o.pay_time,
        DATE(o.create_time) AS order_date,
        HOUR(o.create_time) AS order_hour,
        WEEKDAY(o.create_time) + 1 AS order_weekday,

        -- 是否有效订单(核心业务标记)
        CASE
            WHEN o.status IN ('paid', 'shipped', 'received') THEN 1
            ELSE 0
        END AS is_valid_order,

        -- 是否首单(窗口函数)
        CASE
            WHEN ROW_NUMBER() OVER (
                PARTITION BY o.user_id
                ORDER BY o.create_time
            ) = 1 THEN 1
            ELSE 0
        END AS is_first_order,

        -- 下单到支付的延迟(分钟)
        CASE
            WHEN o.pay_time IS NOT NULL THEN
                TIMESTAMPDIFF(MINUTE, o.create_time, o.pay_time)
            ELSE NULL
        END AS pay_latency_min
    FROM ods_orders o
    LEFT JOIN ods_users u ON o.user_id = u.user_id
    """

    cursor.execute(insert_sql)
    conn.commit()

    # 3. 验证
    cursor.execute("SELECT COUNT(*) FROM dwd_orders")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dwd_orders WHERE is_valid_order = 1")
    valid = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dwd_orders WHERE is_first_order = 1")
    first = cursor.fetchone()[0]

    elapsed = time.time() - t0
    print(f"  ✓ 完成,耗时 {elapsed:.1f}s")
    print(f"    总订单数: {total:,}")
    print(f"    有效订单: {valid:,} ({valid/total*100:.1f}%)")
    print(f"    首单数: {first:,} (应该 ≈ 用户数)")

    cursor.close()


def build_dwd_order_items(conn):
    """
    从 ODS 构建 DWD 订单明细
    包含:
      - 商品维度退化(product_name, category, brand)
      - 订单维度退化(user_id, order_time, is_valid_order)
    """
    print("\n[2/2] 构建 dwd_order_items...")
    t0 = time.time()

    cursor = conn.cursor()

    # 1. 清空
    cursor.execute("TRUNCATE TABLE dwd_order_items")

    # 2. 插入数据
    insert_sql = """
    INSERT INTO dwd_order_items (
        order_id, product_id, quantity, unit_price, amount,
        product_name, category, sub_category, brand,
        user_id, order_time, is_valid_order
    )
    SELECT
        oi.order_id,
        oi.product_id,
        oi.quantity,
        oi.unit_price,
        oi.amount,
        p.product_name,
        p.category,
        p.sub_category,
        p.brand,
        o.user_id,
        o.create_time AS order_time,
        CASE
            WHEN o.status IN ('paid', 'shipped', 'received') THEN 1
            ELSE 0
        END AS is_valid_order
    FROM ods_order_items oi
    JOIN ods_orders o ON oi.order_id = o.order_id
    LEFT JOIN ods_products p ON oi.product_id = p.product_id
    """

    cursor.execute(insert_sql)
    conn.commit()

    # 3. 验证
    cursor.execute("SELECT COUNT(*) FROM dwd_order_items")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dwd_order_items WHERE is_valid_order = 1")
    valid = cursor.fetchone()[0]

    elapsed = time.time() - t0
    print(f"  ✓ 完成,耗时 {elapsed:.1f}s")
    print(f"    总明细数: {total:,}")
    print(f"    有效明细: {valid:,} ({valid/total*100:.1f}%)")

    cursor.close()


def main():
    print("=" * 60)
    print("DWD 层数据接入 - 从 ODS 清洗后写入")
    print("=" * 60)
    print()
    print(f"MySQL: {MYSQL['host']}:{MYSQL['port']} / {MYSQL['database']}")
    print()

    # 1. 创建表
    print("[0] 创建 DWD 表...")
    conn = pymysql.connect(**MYSQL)
    execute_sql(conn, DDL_DWD_ORDERS, "dwd_orders")
    execute_sql(conn, DDL_DWD_ORDER_ITEMS, "dwd_order_items")
    print("    ✓ 2 张表创建完成")
    print()

    # 2. 接入数据
    build_dwd_orders(conn)
    build_dwd_order_items(conn)

    conn.close()

    print()
    print("=" * 60)
    print("✅ DWD 层构建完成!")
    print("=" * 60)
    print()
    print("接下来:")
    print("  1. 跑 test_dwd.py 验证数据")
    print("  2. 打开 queries/dwd_queries.sql 练手")
    print("  3. 重点练 queries/interview_questions.sql 的留存/漏斗/复购")
    print()
    print("DBeaver 里看:")
    print(f"  数据库: {MYSQL['database']}")
    print("  表: dwd_orders, dwd_order_items")


if __name__ == "__main__":
    main()
