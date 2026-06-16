"""
ODS 层数据接入脚本
作用:把 01-data-generation/data/ 下的 CSV 导入 DuckDB
数据流向:
  CSV (原始业务数据)
   ↓
  DuckDB ods.duckdb (ODS 层)
   ↓
  后续 DWD 层从这里取
"""

import os
from pathlib import Path

import duckdb
import pandas as pd

# 路径配置
SCRIPT_DIR = Path(__file__).parent
ODS_DIR = SCRIPT_DIR.parent
PROJECT_DIR = ODS_DIR.parent
DATA_DIR = PROJECT_DIR / "01-data-generation" / "data"
DUCKDB_FILE = ODS_DIR / "ods.duckdb"
DDL_DIR = ODS_DIR / "ddl"

# 数据源配置:文件名 -> 表明
DATA_SOURCES = {
    "users.csv": "ods_users",
    "products.csv": "ods_products",
    "orders.csv": "ods_orders",
    "order_items.csv": "ods_order_items",
}


def execute_ddl_file(con, sql_file: Path):
    """执行一个 DDL SQL 文件"""
    print(f"  → 执行 DDL: {sql_file.name}")
    sql = sql_file.read_text(encoding="utf-8")
    con.execute(sql)


def load_csv_to_table(con, csv_file: Path, table_name: str):
    """把 CSV 导入到指定表"""
    if not csv_file.exists():
        print(f"  ✗ 文件不存在: {csv_file}")
        return 0

    # 用 pandas 读,简单清洗
    print(f"  → 读取 CSV: {csv_file.name}")
    df = pd.read_csv(csv_file)
    print(f"    行数: {len(df):,}, 列数: {len(df.columns)}")

    # 清空表(ODS 层每次全量刷新)
    con.execute(f"DELETE FROM {table_name}")

    # 导入数据
    con.execute(f"INSERT INTO {table_name} SELECT * FROM df")

    # 验证
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"    ✓ 导入完成,当前 {table_name} 表共 {count:,} 行")
    return count


def show_summary(con):
    """显示各表的行数统计"""
    print()
    print("=" * 50)
    print("ODS 层数据汇总")
    print("=" * 50)
    tables = con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name"
    ).fetchall()
    for (table,) in tables:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table:25s} {count:>12,} 行")
    print()


def main():
    print("=" * 50)
    print("ODS 层数据接入 - DuckDB")
    print("=" * 50)
    print()

    # 0. 准备工作
    if not DATA_DIR.exists():
        print(f"[错误] 找不到数据目录: {DATA_DIR}")
        print("       请先跑 01-data-generation/run_all.py 生成数据")
        return 1

    # 1. 连接 DuckDB(自动创建文件)
    print(f"[1] 连接 DuckDB: {DUCKDB_FILE}")
    con = duckdb.connect(str(DUCKDB_FILE))
    print("    ✓ 连接成功")
    print()

    # 2. 建表(执行所有 DDL)
    print("[2] 建表(执行 DDL)")
    ddl_files = [
        DDL_DIR / "ods_users.sql",
        DDL_DIR / "ods_products.sql",
        DDL_DIR / "ods_orders.sql",
        DDL_DIR / "ods_order_items.sql",
    ]
    for ddl_file in ddl_files:
        execute_ddl_file(con, ddl_file)
    print()

    # 3. 导入数据
    print("[3] 导入 CSV 数据")
    total = 0
    for csv_name, table_name in DATA_SOURCES.items():
        csv_path = DATA_DIR / csv_name
        n = load_csv_to_table(con, csv_path, table_name)
        total += n or 0
    print()

    # 4. 汇总
    show_summary(con)

    # 5. 几个验证查询
    print("[4] 验证查询")
    result = con.execute("""
        SELECT status, COUNT(*) AS cnt
        FROM ods_orders
        GROUP BY status
        ORDER BY cnt DESC
    """).df()
    print("订单状态分布:")
    print(result.to_string(index=False))
    print()

    con.close()
    print(f"✅ 完成!DuckDB 文件: {DUCKDB_FILE}")
    print()
    print("下一步:")
    print("  1. 打开 queries/ods_queries.sql 跑几个查询练手")
    print("  2. 学习 SQL 窗口函数")
    print("  3. 准备进入 DWD 层(下周内容)")

    return 0


if __name__ == "__main__":
    exit(main())
