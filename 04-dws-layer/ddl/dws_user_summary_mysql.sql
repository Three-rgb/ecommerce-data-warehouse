-- DWS 用户宽表
-- 粒度:一行 = 一个用户
-- 来源:dwd_orders + dwd_order_items + dwd_orders(品类偏好)

CREATE TABLE dws_user_summary (
    user_id            VARCHAR(20) NOT NULL  COMMENT '用户ID',
    username           VARCHAR(100)          COMMENT '用户名',
    city               VARCHAR(50)           COMMENT '城市',
    user_level         VARCHAR(20)           COMMENT '用户等级',

    -- 基础指标
    total_orders       INT                   COMMENT '总订单数',
    valid_orders       INT                   COMMENT '有效订单数(已支付/已发货/已收货)',
    total_quantity     INT                   COMMENT '累计购买件数',
    total_amount       DECIMAL(15, 2)        COMMENT '累计消费金额',

    -- 时间指标
    first_order_date   DATE                  COMMENT '首单日期',
    last_order_date    DATE                  COMMENT '尾单日期',
    days_since_last    INT                   COMMENT '距今天数(0=今天下单)',
    active_days        INT                   COMMENT '活跃天数(有订单的不同日期数)',

    -- 平均指标
    avg_order_amount   DECIMAL(10, 2)        COMMENT '客单价',
    avg_days_between   DECIMAL(10, 2)        COMMENT '平均下单间隔(天)',

    -- RFM 评分(1-5 分,5 分最好)
    r_score            TINYINT               COMMENT 'R 评分:最近消费(5最好)',
    f_score            TINYINT               COMMENT 'F 评分:消费频次(5最好)',
    m_score            TINYINT               COMMENT 'M 评分:消费金额(5最好)',
    rfm_score          VARCHAR(10)           COMMENT 'RFM 三位分数,如 543',

    -- 客户分层(8 类)
    rfm_segment        VARCHAR(50)           COMMENT '客户分类标签',

    -- 偏好(行为)
    favorite_category  VARCHAR(50)           COMMENT '购买最多的品类',
    favorite_category_amount DECIMAL(15, 2)  COMMENT '该品类的消费金额',

    -- 复购
    is_repurchase      TINYINT               COMMENT '是否复购(2 单及以上)',

    PRIMARY KEY (user_id),
    KEY idx_rfm_segment (rfm_segment),
    KEY idx_r_score (r_score),
    KEY idx_m_score (m_score),
    KEY idx_city (city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 用户宽表';
