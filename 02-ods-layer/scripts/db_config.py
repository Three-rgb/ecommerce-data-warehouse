"""
数据库配置
统一管理 MySQL 连接信息
"""

# MySQL 连接配置
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "charset": "utf8mb4",
}

# 数据库名(会自动创建)
DATABASE_NAME = "ecommerce_dw"

# 拼接 SQLAlchemy URL
def get_mysql_url(database: str = None) -> str:
    """
    生成 SQLAlchemy 用的 MySQL 连接 URL
    用法:
        engine = create_engine(get_mysql_url("ecommerce_dw"))
    """
    db_part = f"/{database}" if database else ""
    cfg = MYSQL_CONFIG
    return (
        f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}{db_part}"
        f"?charset={cfg['charset']}"
    )


# 快速测试
if __name__ == "__main__":
    print("MySQL URL:", get_mysql_url(DATABASE_NAME))
