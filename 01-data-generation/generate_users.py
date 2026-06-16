"""
生成用户数据 (users.csv)
字段:user_id, username, gender, age, city, register_date, level, phone
规模:10 万
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

# 初始化
fake = Faker("zh_CN")  # 中文数据
random.seed(42)
Faker.seed(42)

# 参数
N_USERS = 100_000  # 10 万用户
# 数据输出目录:优先用环境变量 DATA_OUTPUT_DIR,否则放到项目下 data/
DATA_OUTPUT_DIR = os.environ.get("DATA_OUTPUT_DIR", str(Path(__file__).parent.parent / "data"))
OUTPUT_DIR = Path(DATA_OUTPUT_DIR)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 城市白名单(主要城市)
CITIES = [
    "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安",
    "南京", "苏州", "天津", "重庆", "长沙", "青岛", "宁波", "无锡",
    "佛山", "东莞", "郑州", "厦门", "福州", "济南", "合肥", "昆明",
]

# 用户等级
LEVELS = ["Bronze", "Silver", "Gold", "Platinum", "Diamond"]
LEVEL_WEIGHTS = [0.5, 0.25, 0.15, 0.07, 0.03]


def generate_user(user_id: int) -> dict:
    """生成单个用户"""
    gender = random.choice(["M", "F"])
    age = random.choices(
        population=[18, 25, 35, 45, 55, 65],
        weights=[5, 35, 30, 18, 9, 3],
        k=1,
    )[0] + random.randint(-2, 2)

    # 注册时间:过去 2 年内
    days_ago = random.randint(0, 730)
    register_date = datetime.now() - timedelta(days=days_ago)

    return {
        "user_id": f"U{user_id:08d}",
        "username": fake.user_name(),
        "gender": gender,
        "age": age,
        "city": random.choice(CITIES),
        "phone": fake.phone_number(),
        "level": random.choices(LEVELS, weights=LEVEL_WEIGHTS, k=1)[0],
        "register_date": register_date.strftime("%Y-%m-%d"),
    }


def main():
    print(f"开始生成 {N_USERS:,} 个用户...")

    users = [generate_user(i + 1) for i in range(N_USERS)]
    df = pd.DataFrame(users)

    # 输出
    output_file = OUTPUT_DIR / "users.csv"
    df.to_csv(output_file, index=False)

    print(f"✅ 完成! 文件: {output_file}")
    print(f"   行数: {len(df):,}")
    print(f"   文件大小: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    print("数据预览:")
    print(df.head())
    print()
    print("字段类型:")
    print(df.dtypes)


if __name__ == "__main__":
    main()
