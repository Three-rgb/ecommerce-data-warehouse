-- MySQL 版 DDL - 订单明细表
DROP TABLE IF EXISTS ods_order_items;

CREATE TABLE ods_order_items (
    order_id    VARCHAR(20)     NOT NULL  COMMENT '订单ID',
    product_id  VARCHAR(20)     NOT NULL  COMMENT '商品ID',
    quantity    INT                      COMMENT '购买数量',
    unit_price  DECIMAL(10, 2)           COMMENT '当时单价(快照价)',
    amount      DECIMAL(12, 2)           COMMENT '该商品小计',
    PRIMARY KEY (order_id, product_id),
    KEY idx_product_id (product_id),
    KEY idx_order_id (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 订单明细表';
