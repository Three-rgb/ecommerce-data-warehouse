-- ODS 用户表
-- 原始数据:01-data-generation/data/users.csv
-- 字段含义:用户基本信息,注册时一次性写入

CREATE TABLE IF NOT EXISTS ods_users (
    user_id       VARCHAR PRIMARY KEY,    -- 用户ID,格式:U00000001
    username      VARCHAR,                -- 用户名
    gender        VARCHAR,                -- 性别:M/F
    age           INTEGER,                -- 年龄
    city          VARCHAR,                -- 城市
    phone         VARCHAR,                -- 手机号
    level         VARCHAR,                -- 等级:Bronze/Silver/Gold/Platinum/Diamond
    register_date DATE                    -- 注册日期
);
