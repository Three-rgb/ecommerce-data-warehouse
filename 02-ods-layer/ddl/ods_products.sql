-- ODS 商品表
-- 原始数据:01-data-generation/data/products.csv

CREATE TABLE IF NOT EXISTS ods_products (
    product_id     VARCHAR PRIMARY KEY,   -- 商品ID,格式:P000001
    product_name   VARCHAR,               -- 商品名称
    category       VARCHAR,               -- 一级分类:服装/3C数码/美妆/食品/家居
    sub_category   VARCHAR,               -- 二级分类
    price          DECIMAL(10, 2),        -- 价格
    brand          VARCHAR,               -- 品牌
    stock          INTEGER,               -- 库存
    on_shelf_date  DATE                   -- 上架日期
);
