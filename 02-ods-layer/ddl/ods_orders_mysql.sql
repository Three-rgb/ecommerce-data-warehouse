-- MySQL 版 DDL - 订单主表
DROP TABLE IF EXISTS ods_orders;

CREATE TABLE ods_orders (
    order_id      VARCHAR(20)     NOT NULL  COMMENT '订单ID,格式:O000000001',
    user_id       VARCHAR(20)              COMMENT '用户ID',
    total_amount  DECIMAL(12, 2)           COMMENT '订单总金额',
    status        VARCHAR(20)              COMMENT '订单状态:paid/shipped/received/refunded/cancelled',
    item_count    INT                      COMMENT '商品件数',
    create_time   DATETIME                 COMMENT '下单时间',
    pay_time      DATETIME                 COMMENT '支付时间',
    PRIMARY KEY (order_id),
    KEY idx_user_id (user_id),
    KEY idx_create_time (create_time),
    KEY idx_status (status),
    KEY idx_user_status_time (user_id, status, create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 订单主表';
