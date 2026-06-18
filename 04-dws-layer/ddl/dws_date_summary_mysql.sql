-- DWS 时间宽表
-- 粒度:一行 = 一天

CREATE TABLE dws_date_summary (
    date               DATE NOT NULL  COMMENT '日期',

    -- 用户指标
    dau                INT           COMMENT '日活跃用户(有效订单)',
    new_users          INT           COMMENT '新客数(首单)',
    repurchase_users   INT           COMMENT '复购用户(2单以上)',
    total_active_users INT          COMMENT '所有活跃用户',

    -- 订单指标
    total_orders       INT           COMMENT '总订单数',
    valid_orders       INT           COMMENT '有效订单数',

    -- 金额指标
    total_amount       DECIMAL(15, 2) COMMENT '日 GMV',
    avg_order_value    DECIMAL(10, 2) COMMENT '客单价',
    avg_user_amount    DECIMAL(10, 2) COMMENT '人均消费',

    -- 时间维度(冗余)
    year               INT,
    month              INT,
    weekday            INT           COMMENT '1-7(周一到周日)',

    PRIMARY KEY (date),
    KEY idx_year_month (year, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS 时间宽表';
