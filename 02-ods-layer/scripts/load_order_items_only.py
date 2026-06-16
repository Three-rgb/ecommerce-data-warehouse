"""
单独导入 ods_order_items 表
"""

import sys
import time
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
DATA_FILE = PROJECT_DIR / "data" / "order_items.csv"

sys.path.insert(0, str(SCRIPT_DIR))
from db_config import get_mysql_url, DATABASE_NAME


def main():
    if not DATA_FILE.exists():
        print(f"[错误] 找不到 {DATA_FILE}")
        return 1
    print("=" * 60)
    print("单独导入 ods_order_items")
    print("=" * 60)
    print()
    engine = create_engine(get_mysql_url(DATABASE_NAME))
    with engine.connect() as conn:
        current = conn.execute(text("SELECT COUNT(*) FROM ods_order_items")).fetchone()[0]
    print(f"当前 ods_order_items 表行数: {current:,}")
    if current > 0:
        print("⚠️  表里已经有数据,先清空再导入")
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE ods_order_items"))
        print("✓ 已清空")
    print()
    print(f"读取 CSV: {DATA_FILE.name}")
    df = pd.read_csv(DATA_FILE)
    print(f"  数据规模: {len(df):,} 行 × {len(df.columns)} 列")
    print()
    print("开始导入(200 万行,预计 2-3 分钟)...")
    t0 = time.time()
    df.to_sql(
        name="ods_order_items",
        con=engine,
        if_exists="append",
        index=False,
        chunksize=5000,
        method="multi",
    )
    elapsed = time.time() - t0
    print(f"  ✓ 导入完成,耗时 {elapsed:.1f}s")
    print()
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM ods_order_items")).fetchone()[0]
    print(f"✅ ods_order_items 表现有 {count:,} 行")
    engine.dispose()
    return 0

if __name__ == "__main__":
    exit(main())