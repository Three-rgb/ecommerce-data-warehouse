"""
生成订单数据 (orders.csv + order_items.csv)
- orders:订单主表(100 万)
- order_items:订单明细(每个订单 1-5 个商品)

订单表字段:order_id, user_id, total_amount, status, pay_time, create_time
明细表字段:order_item_id, order_id, product_id, quantity, unit_price, amount
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from tqdm import tqdm

random.seed(44)

# 参数
N_ORDERS = 1_000_000  # 100 万订单
N_USERS = 100_000  # 用户数
N_PRODUCTS = 5_000  # 商品数
BATCH_SIZE = 50_000  # 每批处理 5 万,避免内存爆

OUTPUT_DIR = Path(__file__).parent.parent / "data"
DATA_OUTPUT_DIR = os.environ.get("DATA_OUTPUT_DIR", str(Path(__file__).parent.parent / "data"))
OUTPUT_DIR = Path(DATA_OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 订单状态(符合业务真实分布)
ORDER_STATUS = ["paid", "shipped", "received", "refunded", "cancelled"]
STATUS_WEIGHTS = [0.65, 0.15, 0.10, 0.05, 0.05]


def generate_one_order(order_id: int, order_items_buffer: list):
    """生成单个订单及其明细"""
    user_id = f"U{random.randint(1, N_USERS):08d}"

    # 订单创建时间:过去 1 年
    days_ago = random.randint(0, 365)
    hours_offset = random.randint(0, 23)
    create_time = datetime.now() - timedelta(days=days_ago, hours=hours_offset)

    status = random.choices(ORDER_STATUS, weights=STATUS_WEIGHTS, k=1)[0]

    # 支付时间(只有 paid/shipped/received/refunded 才有)
    if status in ["paid", "shipped", "received", "refunded"]:
        pay_time = create_time + timedelta(minutes=random.randint(1, 30))
    else:
        pay_time = None  # 未支付

    # 每个订单 1-5 个商品
    n_items = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5], k=1)[0]

    # 关键修复:用 sample 不重复选商品
    # 真实业务里,同一个订单里同一个商品只能出现一次(数量在 quantity 里体现)
    selected_product_ids = random.sample(range(1, N_PRODUCTS + 1), n_items)

    total_amount = 0.0
    for product_id_int in selected_product_ids:
        product_id = f"P{product_id_int:06d}"
        unit_price = round(random.lognormvariate(5.0, 1.0), 2)  # 价格分布
        unit_price = max(5.0, min(unit_price, 5000.0))  # 限价
        quantity = random.choices([1, 2, 3, 4, 5], weights=[60, 20, 10, 5, 5], k=1)[0]
        amount = round(unit_price * quantity, 2)
        total_amount += amount

        order_items_buffer.append(
            {
                "order_id": f"O{order_id:09d}",
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
            }
        )

    return {
        "order_id": f"O{order_id:09d}",
        "user_id": user_id,
        "total_amount": round(total_amount, 2),
        "status": status,
        "item_count": n_items,
        "create_time": create_time.strftime("%Y-%m-%d %H:%M:%S"),
        "pay_time": pay_time.strftime("%Y-%m-%d %H:%M:%S") if pay_time else "",
    }


def main():
    print(f"开始生成 {N_ORDERS:,} 个订单...")
    print(f"预计生成 {N_ORDERS * 3:,} 条订单明细(平均每单 3 件)")
    print()

    orders_file = OUTPUT_DIR / "orders.csv"
    items_file = OUTPUT_DIR / "order_items.csv"

    # 写文件头
    orders_header = [
        "order_id",
        "user_id",
        "total_amount",
        "status",
        "item_count",
        "create_time",
        "pay_time",
    ]
    items_header = ["order_id", "product_id", "quantity", "unit_price", "amount"]

    orders_f = open(orders_file, "w", encoding="utf-8")
    items_f = open(items_file, "w", encoding="utf-8")

    orders_f.write(",".join(orders_header) + "\n")
    items_f.write(",".join(items_header) + "\n")

    total_items = 0
    try:
        for batch_start in range(0, N_ORDERS, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, N_ORDERS)
            items_buffer = []

            for order_id in range(batch_start + 1, batch_end + 1):
                order = generate_one_order(order_id, items_buffer)
                orders_f.write(",".join(str(v) for v in order.values()) + "\n")

            # 写明细
            for item in items_buffer:
                items_f.write(",".join(str(v) for v in item.values()) + "\n")
            total_items += len(items_buffer)

            pct = batch_end / N_ORDERS * 100
            print(f"  进度: {batch_end:,} / {N_ORDERS:,} ({pct:.0f}%)")

    finally:
        orders_f.close()
        items_f.close()

    print()
    print("✅ 完成!")
    print(f"   订单表: {orders_file}")
    print(f"   订单明细表: {items_file}")
    print(f"   订单数: {N_ORDERS:,}")
    print(f"   明细数: {total_items:,}")
    print(f"   订单文件大小: {orders_file.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"   明细文件大小: {items_file.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
