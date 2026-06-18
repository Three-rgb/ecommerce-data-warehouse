-- ============================================
-- 面试必考 SQL 题(数仓岗)
-- 重点:留存率、转化漏斗、复购分析
-- ============================================

-- ============================================
-- 第 1 题:计算每日新用户数
-- ============================================
SELECT
    order_date,
    COUNT(DISTINCT user_id) AS new_user_count
FROM dwd_orders
WHERE is_first_order = 1 AND is_valid_order = 1
GROUP BY order_date
ORDER BY order_date
LIMIT 30;


-- ============================================
-- 第 2 题:次日 / 7 日 / 30 日留存率
-- 这道题几乎 100% 必考!
-- ============================================
WITH first_orders AS (
    -- 每个用户的首单日期
    SELECT
        user_id,
        MIN(order_date) AS first_date
    FROM dwd_orders
    WHERE is_valid_order = 1
    GROUP BY user_id
),
user_activity AS (
    -- 每个用户每天是否活跃
    SELECT DISTINCT
        user_id,
        order_date
    FROM dwd_orders
    WHERE is_valid_order = 1
)
SELECT
    f.first_date,
    COUNT(DISTINCT f.user_id) AS new_users,
    -- 次日留存
    COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) = 1 THEN f.user_id
    END) AS d1_retained,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) = 1 THEN f.user_id
    END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS d1_retention_pct,
    -- 7 日留存
    COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) BETWEEN 1 AND 7 THEN f.user_id
    END) AS d7_retained,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) BETWEEN 1 AND 7 THEN f.user_id
    END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS d7_retention_pct,
    -- 30 日留存
    COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) BETWEEN 1 AND 30 THEN f.user_id
    END) AS d30_retained,
    ROUND(COUNT(DISTINCT CASE
        WHEN DATEDIFF(u.order_date, f.first_date) BETWEEN 1 AND 30 THEN f.user_id
    END) * 100.0 / COUNT(DISTINCT f.user_id), 2) AS d30_retention_pct
FROM first_orders f
LEFT JOIN user_activity u ON f.user_id = u.user_id
GROUP BY f.first_date
ORDER BY f.first_date
LIMIT 30;


-- ============================================
-- 第 3 题:转化漏斗
-- 用订单状态模拟:下单 → 支付 → 发货 → 收货
-- ============================================
SELECT
    -- 第 1 步:总下单用户
    COUNT(DISTINCT user_id) AS step1_total_users,
    -- 第 2 步:已支付用户
    COUNT(DISTINCT CASE WHEN status IN ('paid', 'shipped', 'received') THEN user_id END) AS step2_paid,
    -- 第 3 步:已发货用户
    COUNT(DISTINCT CASE WHEN status IN ('shipped', 'received') THEN user_id END) AS step3_shipped,
    -- 第 4 步:已收货用户
    COUNT(DISTINCT CASE WHEN status = 'received' THEN user_id END) AS step4_received
FROM dwd_orders
WHERE is_valid_order = 1 OR status IN ('cancelled', 'refunded');


-- ============================================
-- 第 4 题:复购率
-- ============================================
WITH user_orders AS (
    SELECT
        user_id,
        COUNT(*) AS order_count
    FROM dwd_orders
    WHERE is_valid_order = 1
    GROUP BY user_id
)
SELECT
    COUNT(*) AS total_buyers,
    SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) AS repurchase_buyers,
    ROUND(SUM(CASE WHEN order_count >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS repurchase_rate_pct
FROM user_orders;


-- ============================================
-- 第 5 题:复购周期分布
-- ============================================
WITH orders_with_prev AS (
    SELECT
        user_id, order_id, create_time,
        LAG(create_time) OVER (PARTITION BY user_id ORDER BY create_time) AS prev_time
    FROM dwd_orders
    WHERE is_valid_order = 1
),
repurchase_intervals AS (
    SELECT
        user_id,
        DATEDIFF(create_time, prev_time) AS days_to_repurchase
    FROM orders_with_prev
    WHERE prev_time IS NOT NULL
)
SELECT
    CASE
        WHEN days_to_repurchase BETWEEN 0 AND 7 THEN '0-7天'
        WHEN days_to_repurchase BETWEEN 8 AND 30 THEN '8-30天'
        WHEN days_to_repurchase BETWEEN 31 AND 90 THEN '31-90天'
        WHEN days_to_repurchase BETWEEN 91 AND 180 THEN '91-180天'
        ELSE '180天以上'
    END AS interval_range,
    COUNT(*) AS repurchase_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) AS pct
FROM repurchase_intervals
GROUP BY interval_range
ORDER BY MIN(days_to_repurchase);


-- ============================================
-- 第 6 题:连续登录/连续下单用户(进阶)
-- 经典面试题:用窗口函数识别连续行为
-- ============================================
WITH daily_orders AS (
    SELECT DISTINCT user_id, order_date
    FROM dwd_orders
    WHERE is_valid_order = 1
),
with_groups AS (
    SELECT
        user_id, order_date,
        -- 关键技巧:order_date - row_number 得到"组号"
        DATE_SUB(order_date, INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY order_date) DAY) AS grp
    FROM daily_orders
),
consecutive_groups AS (
    SELECT
        user_id, grp,
        COUNT(*) AS consecutive_days,
        MIN(order_date) AS start_date,
        MAX(order_date) AS end_date
    FROM with_groups
    GROUP BY user_id, grp
)
SELECT
    consecutive_days,
    COUNT(*) AS user_count
FROM consecutive_groups
WHERE consecutive_days >= 3  -- 至少连续 3 天
GROUP BY consecutive_days
ORDER BY consecutive_days;


-- ============================================
-- 第 7 题:每月新客 vs 老客消费对比
-- ============================================
WITH monthly_orders AS (
    SELECT
        DATE_FORMAT(order_date, '%Y-%m') AS month,
        user_id,
        is_first_order,
        total_amount
    FROM dwd_orders
    WHERE is_valid_order = 1
)
SELECT
    month,
    COUNT(DISTINCT CASE WHEN is_first_order = 1 THEN user_id END) AS new_buyers,
    COUNT(DISTINCT CASE WHEN is_first_order = 0 THEN user_id END) AS returning_buyers,
    ROUND(SUM(CASE WHEN is_first_order = 1 THEN total_amount ELSE 0 END), 2) AS new_buyer_gmv,
    ROUND(SUM(CASE WHEN is_first_order = 0 THEN total_amount ELSE 0 END), 2) AS returning_buyer_gmv
FROM monthly_orders
GROUP BY month
ORDER BY month;
