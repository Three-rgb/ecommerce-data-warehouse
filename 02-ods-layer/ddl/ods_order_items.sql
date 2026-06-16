-- ODS 订单明细表
-- 原始数据:01-data-generation/data/order_items.csv
-- 粒度:一行 = 订单中的一个商品

CREATE TABLE IF NOT EXISTS ods_order_items (
    order_id    VARCHAR,                  -- 订单ID(联合主键 1)
    product_id  VARCHAR,                  -- 商品ID(联合主键 2)
    quantity    INTEGER,                  -- 购买数量
    unit_price  DECIMAL(10, 2),           -- 当时单价(快照价)
    amount      DECIMAL(12, 2),           -- 该商品小计金额
    PRIMARY KEY (order_id, product_id)
);
