"""
ODS 层 MySQL 数据接入脚本
作用:把 CSV 数据导入 MySQL 的 ecommerce_dw 数据库

数据流:
  CSV (01-data-generation/data/)
   ↓
  MySQL ecommerce_dw.ods_*
   ↓
  DWD 层从这里取数
"""

import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

# 路径配置
SCRIPT_DIR = Path(__file__).parent
ODS_DIR = SCRIPT_DIR.parent
PROJECT_DIR = ODS_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DDL_DIR = ODS_DIR / "ddl"

sys.path.insert(0, str(SCRIPT_DIR))
from db_config import MYSQL_CONFIG, DATABASE_NAME, get_mysql_url  # noqa


def create_database_if_not_exists():
    """先连 MySQL(不指定数据库),创建 ecommerce_dw"""
    print(f"[1/4] 创建数据库 {DATABASE_NAME}...")
    engine = create_engine(get_mysql_url(), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        # utf8mb4 是 MySQL 真正的 UTF-8
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
    engine.dispose()
    print(f"    ✓ 数据库 {DATABASE_NAME} 就绪")


def execute_ddl(engine):
    """执行所有 DDL 文件,创建表结构"""
    print(f"[2/4] 创建表结构...")
    ddl_files = [
        DDL_DIR / "ods_users_mysql.sql",
        DDL_DIR / "ods_products_mysql.sql",
        DDL_DIR / "ods_orders_mysql.sql",
        DDL_DIR / "ods_order_items_mysql.sql",
    ]
    with engine.connect() as conn:
        for ddl_file in ddl_files:
            print(f"  → 执行 {ddl_file.name}")
            sql = ddl_file.read_text(encoding="utf-8")
            # 一次执行一个文件(DROP + CREATE)
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
    print(f"    ✓ 4 张表创建完成")


def load_csv_to_table(engine, csv_file: Path, table_name: str, chunksize: int = 10000):
    """把 CSV 导入到 MySQL 表"""
    if not csv_file.exists():
        print(f"  ✗ 文件不存在: {csv_file}")
        return 0

    print(f"  → {csv_file.name} → {table_name}")
    df = pd.read_csv(csv_file)
    print(f"    数据规模: {len(df):,} 行 × {len(df.columns)} 列")

    # 处理时间字段
    for col in df.columns:
        if "time" in col.lower() or "date" in col.lower():
            if df[col].dtype == "object":
                # 空字符串转 None
                df[col] = df[col].replace("", None)
                # 尝试转 datetime
                try:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    pass

    t0 = time.time()
    # to_sql 分批导入,避免锁表太久
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="append",
        index=False,
        chunksize=chunksize,
        method="multi",  # 批量插入,快
    )
    elapsed = time.time() - t0

    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()[0]
    print(f"    ✓ 导入 {count:,} 行,耗时 {elapsed:.1f}s")
    return count


def show_summary(engine):
    """显示各表的行数统计"""
    print()
    print("=" * 50)
    print(f"📊 {DATABASE_NAME} 数据库表数据汇总")
    print("=" * 50)
    with engine.connect() as conn:
        rows = conn.execute(
            text("SHOW TABLES")
        ).fetchall()
        for (table,) in rows:
            count = conn.execute(
                text(f"SELECT COUNT(*) FROM `{table}`")
            ).fetchone()[0]
            print(f"  {table:25s} {count:>12,} 行")
    print()


def main():
    print("=" * 60)
    print("ODS 层数据接入 - MySQL")
    print("=" * 60)
    print()
    print(f"目标 MySQL: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    print(f"目标数据库: {DATABASE_NAME}")
    print()

    if not DATA_DIR.exists():
        print(f"[错误] 找不到数据目录: {DATA_DIR}")
        print("       请先跑 01-data-generation/run_all.py 生成数据")
        return 1

    # 第 1 步:创建数据库
    create_database_if_not_exists()
    print()

    # 创建连接(指定数据库)
    engine = create_engine(get_mysql_url(DATABASE_NAME))

    # 第 2 步:建表
    execute_ddl(engine)
    print()

    # 第 3 步:导入数据
    print(f"[3/4] 导入 CSV 数据")
    sources = [
        ("users.csv", "ods_users"),
        ("products.csv", "ods_products"),
        ("orders.csv", "ods_orders"),
        ("order_items.csv", "ods_order_items"),
    ]
    for csv_name, table_name in sources:
        load_csv_to_table(engine, DATA_DIR / csv_name, table_name)
    print()

    # 第 4 步:汇总
    show_summary(engine)

    engine.dispose()

    print("✅ 完成!现在你可以:")
    print()
    print("  1. 在 DBeaver 里连接 MySQL,看 ecommerce_dw 数据库")
    print("  2. 跑 test_ods_mysql.py 做几个验证查询")
    print("  3. 用 SQL 学习窗口函数")
    print()
    print("DBeaver 连接参数:")
    print(f"  主机: {MYSQL_CONFIG['host']}")
    print(f"  端口: {MYSQL_CONFIG['port']}")
    print(f"  用户: {MYSQL_CONFIG['user']}")
    print(f"  数据库: {DATABASE_NAME}")
    return 0


if __name__ == "__main__":
    exit(main())
