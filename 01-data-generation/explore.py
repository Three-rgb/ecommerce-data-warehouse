from pathlib import Path
import pandas as pd

# 项目根目录（脚本位于 01-data-generation/，所以向上跳一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 读数据（绝对路径，跨机器/跨工作目录都能跑）
orders = pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["create_time"])
users = pd.read_csv(DATA_DIR / "users.csv")

print("=" * 50)
print("订单总量:", f"{len(orders):,}")
print("=" * 50)
print()
print("订单状态分布:")
print(orders["status"].value_counts())
print()
print("客单价:", round(orders["total_amount"].mean(), 2), "元")
print("最高单笔:", round(orders["total_amount"].max(), 2), "元")
print("最低单笔:", round(orders["total_amount"].min(), 2), "元")
print()
print("用户量:", f"{len(users):,}")
print("用户城市 Top 5:")
print(users["city"].value_counts().head())
print()
print("订单时间范围:")
print("  最早:", orders["create_time"].min())
print("  最晚:", orders["create_time"].max())