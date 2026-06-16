"""
单独导入 ods_order_items 表 - 纯 pymysql 版本
绕开 SQLAlchemy 2.0 + pandas to_sql 的兼容性问题
"""

import csv
import sys
import time
from pathlib import Path
import pymysql

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
DATA_FILE = PROJECT_DIR / "data" / "order_items.csv"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "ecommerce_dw",
    "charset": "utf8mb4",
}

BATCH_SIZE = 1000


def main():
    if not DATA_FILE.exists():
        print(f"[错误] 找不到 {DATA_FILE}")
        return 1
    print("=" * 60)
    print("单独导入 ods_order_items - pymysql executemany 版本")
    print("=" * 60)
    print()
    print("[1] 连接 MySQL...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    print("    ✓ 连接成功")
    print()
    print("[2] 清空 ods_order_items 表...")
    cursor.execute("TRUNCATE TABLE ods_order_items")
    conn.commit()
    print("    ✓ 已清空")
    print()
    print(f"[3] 读取并插入 {DATA_FILE.name}")
    print(f"    每批 {BATCH_SIZE} 行(参数数 {BATCH_SIZE*5},绝对安全)")
    print()
    insert_sql = """
    INSERT INTO ods_order_items
    (order_id, product_id, quantity, unit_price, amount)
    VALUES (%s, %s, %s, %s, %s)
    """
    t0 = time.time()
    total_inserted = 0
    batch = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"    CSV 表头: {header}")
        print()
        for row in reader:
            batch.append(tuple(row))
            if len(batch) >= BATCH_SIZE:
                cursor.executemany(insert_sql, batch)
                conn.commit()
                total_inserted += len(batch)
                batch = []
                if total_inserted % 50000 == 0:
                    elapsed = time.time() - t0
                    speed = total_inserted / elapsed
                    print(
                        f"    进度: {total_inserted:>10,} 行  "
                        f"({total_inserted/2099219*100:.0f}%)  "
                        f"速度: {speed:>6,.0f} 行/秒"
                    )
        if batch:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            total_inserted += len(batch)
    elapsed = time.time() - t0
    print()
    print(f"    ✓ 导入完成!共 {total_inserted:,} 行,耗时 {elapsed:.1f} 秒")
    print()
    print("[4] 验证...")
    cursor.execute("SELECT COUNT(*) FROM ods_order_items")
    count = cursor.fetchone()[0]
    print(f"    数据库里 ods_order_items 表现有: {count:,} 行")
    print()
    cursor.execute("SELECT * FROM ods_order_items LIMIT 5")
    print("    前 5 条数据:")
    for row in cursor.fetchall():
        print(f"      {row}")
    print()
    cursor.close()
    conn.close()
    print("=" * 60)
    print("✅ 完成!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())