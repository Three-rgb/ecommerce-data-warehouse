"""
一键运行所有数据生成脚本
用法:python run_all.py
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run_script(script_name: str):
    """运行指定的 Python 脚本"""
    script_path = SCRIPT_DIR / script_name
    print("=" * 60)
    print(f"▶ 正在运行: {script_name}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(SCRIPT_DIR),
    )

    if result.returncode != 0:
        print(f"❌ {script_name} 运行失败!")
        sys.exit(1)
    print()


def main():
    print("🚀 开始生成电商数仓的全部数据...")
    print()

    # 按依赖顺序运行
    run_script("generate_users.py")
    run_script("generate_products.py")
    run_script("generate_orders.py")

    # 显示最终结果
    data_dir = SCRIPT_DIR.parent / "data"
    print("=" * 60)
    print("🎉 全部数据生成完成!")
    print("=" * 60)
    print()
    print("生成的文件:")
    for f in sorted(data_dir.glob("*.csv")):
        size_mb = f.stat().st_size / 1024 / 1024
        print(f"  📄 {f.name:25s}  {size_mb:8.1f} MB")
    print()
    print("下一步:")
    print("  1. 打开 data/ 目录看看生成的数据")
    print("  2. 用 pandas 读 CSV 做几个简单统计")
    print("  3. 参考 docs/week1.md 完成任务")


if __name__ == "__main__":
    main()
