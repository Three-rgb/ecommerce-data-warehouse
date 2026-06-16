-- ODS 订单主表
-- 原始数据:01-data-generation/data/orders.csv
-- 粒度:一行 = 一个订单

CREATE TABLE IF NOT EXISTS ods_orders (
    order_id      VARCHAR PRIMARY KEY,    -- 订单ID,格式:O000000001
    user_id       VARCHAR,                -- 下单用户ID(外键,ODS 不强制约束)
    total_amount  DECIMAL(12, 2),         -- 订单总金额
    status        VARCHAR,                -- 订单状态:paid/shipped/received/refunded/cancelled
    item_count    INTEGER,                -- 商品件数
    create_time   TIMESTAMP,              -- 下单时间
    pay_time      TIMESTAMP               -- 支付时间(空表示未支付)
);

-- ODS 层一般会建索引,这里 DuckDB 暂时不显式建(自动优化)
-- 真 MySQL 里会加:
-- CREATE INDEX idx_user_id ON ods_orders(user_id);
-- CREATE INDEX idx_create_time ON ods_orders(create_time);
-- CREATE INDEX idx_status ON ods_orders(status);
