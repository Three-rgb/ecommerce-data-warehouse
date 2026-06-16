"""
生成商品数据 (products.csv)
字段:product_id, product_name, category, sub_category, price, brand, stock
规模:5 千
"""

import os
import random
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker("zh_CN")
random.seed(43)
Faker.seed(43)

# 参数
N_PRODUCTS = 5_000
# 数据输出目录:优先用环境变量 DATA_OUTPUT_DIR
DATA_OUTPUT_DIR = os.environ.get("DATA_OUTPUT_DIR", str(Path(__file__).parent.parent / "data"))
OUTPUT_DIR = Path(DATA_OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 商品分类
CATEGORIES = {
    "服装": {
        "sub_categories": ["男装", "女装", "童装", "运动装", "内衣"],
        "brands": ["优衣库", "ZARA", "H&M", "Nike", "Adidas", "李宁", "安踏"],
        "price_range": (50, 2000),
    },
    "3C数码": {
        "sub_categories": ["手机", "电脑", "平板", "耳机", "智能手表", "相机"],
        "brands": ["Apple", "华为", "小米", "OPPO", "vivo", "联想", "戴尔"],
        "price_range": (200, 15000),
    },
    "美妆": {
        "sub_categories": ["护肤", "彩妆", "香水", "面膜", "洗护"],
        "brands": ["兰蔻", "雅诗兰黛", "SK-II", "资生堂", "完美日记", "花西子"],
        "price_range": (30, 3000),
    },
    "食品": {
        "sub_categories": ["零食", "饮料", "生鲜", "茶叶", "酒水", "调味品"],
        "brands": ["三只松鼠", "良品铺子", "百草味", "农夫山泉", "可口可乐"],
        "price_range": (10, 500),
    },
    "家居": {
        "sub_categories": ["床上用品", "厨房用品", "收纳", "清洁", "灯具"],
        "brands": ["宜家", "罗莱", "水星家纺", "双立人", "苏泊尔"],
        "price_range": (20, 5000),
    },
}


def generate_product(product_id: int) -> dict:
    """生成单个商品"""
    category = random.choice(list(CATEGORIES.keys()))
    cat_info = CATEGORIES[category]

    sub_category = random.choice(cat_info["sub_categories"])
    brand = random.choice(cat_info["brands"])
    price_min, price_max = cat_info["price_range"]

    # 价格服从对数正态分布(便宜的多,贵的少)
    import math
    log_price = random.uniform(math.log(price_min), math.log(price_max))
    price = round(math.exp(log_price), 2)

    return {
        "product_id": f"P{product_id:06d}",
        "product_name": f"{brand} {sub_category} {fake.word()}",
        "category": category,
        "sub_category": sub_category,
        "price": price,
        "brand": brand,
        "stock": random.randint(0, 10000),
        "on_shelf_date": fake.date_between(start_date="-2y", end_date="today").strftime(
            "%Y-%m-%d"
        ),
    }


def main():
    print(f"开始生成 {N_PRODUCTS:,} 个商品...")

    products = [generate_product(i + 1) for i in range(N_PRODUCTS)]
    df = pd.DataFrame(products)

    output_file = OUTPUT_DIR / "products.csv"
    df.to_csv(output_file, index=False)

    print(f"✅ 完成! 文件: {output_file}")
    print(f"   行数: {len(df):,}")
    print(f"   文件大小: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("各分类商品数:")
    print(df["category"].value_counts())
    print()
    print("价格分布:")
    print(df["price"].describe())


if __name__ == "__main__":
    main()
