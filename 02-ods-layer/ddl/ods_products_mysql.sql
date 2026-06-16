-- MySQL 版 DDL - 商品表
DROP TABLE IF EXISTS ods_products;

CREATE TABLE ods_products (
    product_id     VARCHAR(20)    NOT NULL  COMMENT '商品ID,格式:P000001',
    product_name   VARCHAR(255)             COMMENT '商品名称',
    category       VARCHAR(50)              COMMENT '一级分类',
    sub_category   VARCHAR(50)              COMMENT '二级分类',
    price          DECIMAL(10, 2)           COMMENT '价格',
    brand          VARCHAR(100)             COMMENT '品牌',
    stock          INT                      COMMENT '库存',
    on_shelf_date  DATE                     COMMENT '上架日期',
    PRIMARY KEY (product_id),
    KEY idx_category (category),
    KEY idx_brand (brand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 商品表';
