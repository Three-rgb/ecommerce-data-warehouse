-- ============================================
-- MySQL 版 DDL - 用户表
-- 字符集:utf8mb4(支持 emoji)
-- 引擎:InnoDB(支持事务)
-- ============================================

DROP TABLE IF EXISTS ods_users;

CREATE TABLE ods_users (
    user_id       VARCHAR(20)  NOT NULL  COMMENT '用户ID,格式:U00000001',
    username      VARCHAR(100)           COMMENT '用户名',
    gender        VARCHAR(2)             COMMENT '性别:M/F',
    age           INT                    COMMENT '年龄',
    city          VARCHAR(50)            COMMENT '城市',
    phone         VARCHAR(20)            COMMENT '手机号',
    level         VARCHAR(20)            COMMENT '等级:Bronze/Silver/Gold/Platinum/Diamond',
    register_date DATE                   COMMENT '注册日期',
    PRIMARY KEY (user_id),
    KEY idx_city (city),
    KEY idx_level (level),
    KEY idx_register_date (register_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS 用户表';
