-- DWS 商品宽表
-- 粒度:一行 = 一个商品

CREATE TABLE dws_product_summary (
    product_id         VARCHAR(20) NOT NULL  COMMENT '商品ID',
    product_name       VARCHAR(255)          COMMENT '商品名称',
    category           VARCHAR(50)           COMMENT '一级分类',
    sub_category       VARCHAR(50)           COMMENT '二级分类',
    brand              VARCHAR(100)          COMMENT '品牌',
    price              DECIMAL(10, 2)        COMMENT '标价',

    -- 销量指标
    total_quantity     INT                   COMMENT '累计销量(件)',
    total_orders       INT                   COMMENT '累计订单数(去重)',
    total_users        INT                   COMMENT '累计购买用户数',
    total_amount       DECIMAL(15, 2)        COMMENT '累计销售额',

    -- 时间指标
    first_sale_date    DATE                  COMMENT '首销日期',
    last_sale_date     DATE                  COMMENT '尾销日期',

    -- 平均指标
    avg_quantity_per_order DECIMAL(10, 2)    COMMENT '平均每订单件数',
    avg_user_quantity  DECIMAL(10, 2)        COMMENT '人均购买件数',

    -- 排名(按品类内)
    category_rank      INT                   COMMENT '品类内销量排名',

    PRIMARY KEY (product_id),
    KEY idx_category (category),
    KEY idx_brand (brand),
    KEY idx_total_amount (total_amount)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 商品宽表';
