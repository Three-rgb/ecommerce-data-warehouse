-- ============================================
-- DWD 层常用查询(10 个)
-- 重点:窗口函数练习
-- ============================================

-- 1. 每个用户的订单序号
-- 重点:ROW_NUMBER() + PARTITION BY
SELECT
    user_id, order_id, create_time, total_amount,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY create_time) AS order_seq
FROM dwd_orders
WHERE is_valid_order = 1
ORDER BY user_id, create_time
LIMIT 20;

-- 2. 累计消费金额
-- 重点:SUM() OVER (ORDER BY ...)
SELECT
    user_id, order_id, create_time, total_amount,
    SUM(total_amount) OVER (PARTITION BY user_id ORDER BY create_time) AS cumulative_spent
FROM dwd_orders
WHERE is_valid_order = 1 AND user_id = 'U00000001'
ORDER BY create_time;

-- 3. 上一笔订单的时间和金额
-- 重点:LAG()
SELECT
    user_id, order_id, create_time, total_amount,
    LAG(create_time) OVER (PARTITION BY user_id ORDER BY create_time) AS prev_order_time,
    LAG(total_amount) OVER (PARTITION BY user_id ORDER BY create_time) AS prev_amount,
    DATEDIFF(create_time, LAG(create_time) OVER (PARTITION BY user_id ORDER BY create_time)) AS days_to_prev
FROM dwd_orders
WHERE is_valid_order = 1
ORDER BY user_id, create_time
LIMIT 20;

-- 4. 每个用户的首单信息
-- 重点:ROW_NUMBER() = 1
SELECT *
FROM dwd_orders
WHERE is_first_order = 1
LIMIT 20;

-- 5. 用户复购周期分析
-- 重点:LAG + DATEDIFF
WITH orders_with_prev AS (
    SELECT
        user_id, order_id, create_time,
        LAG(create_time) OVER (PARTITION BY user_id ORDER BY create_time) AS prev_time
    FROM dwd_orders
    WHERE is_valid_order = 1
)
SELECT
    user_id,
    AVG(DATEDIFF(create_time, prev_time)) AS avg_days_to_repurchase,
    COUNT(*) AS repurchase_count
FROM orders_with_prev
WHERE prev_time IS NOT NULL
GROUP BY user_id
ORDER BY avg_days_to_repurchase
LIMIT 20;

-- 6. RFM 模型基础
-- R(Recency):最近一次消费距今多少天
-- F(Frequency):消费频次
-- M(Monetary):消费金额
WITH rfm AS (
    SELECT
        user_id,
        DATEDIFF(CURDATE(), MAX(create_time)) AS R,
        COUNT(*) AS F,
        SUM(total_amount) AS M
    FROM dwd_orders
    WHERE is_valid_order = 1
    GROUP BY user_id
)
SELECT
    *,
    CASE
        WHEN R <= 30 THEN '高'
        WHEN R <= 90 THEN '中'
        ELSE '低'
    END AS R_level,
    CASE
        WHEN F >= 5 THEN '高'
        WHEN F >= 2 THEN '中'
        ELSE '低'
    END AS F_level,
    CASE
        WHEN M >= 5000 THEN '高'
        WHEN M >= 1000 THEN '中'
        ELSE '低'
    END AS M_level
FROM rfm
LIMIT 20;

-- 7. 各品类的销售排名
-- 重点:DENSE_RANK()
SELECT
    category, brand, total_sales,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_sales DESC) AS brand_rank_in_category
FROM (
    SELECT
        category, brand,
        SUM(amount) AS total_sales
    FROM dwd_order_items
    WHERE is_valid_order = 1
    GROUP BY category, brand
) t
ORDER BY category, brand_rank_in_category
LIMIT 30;

-- 8. 月度 GMV 趋势
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS month,
    COUNT(DISTINCT order_id) AS order_count,
    COUNT(DISTINCT user_id) AS active_users,
    ROUND(SUM(total_amount), 2) AS gmv,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM dwd_orders
WHERE is_valid_order = 1
GROUP BY month
ORDER BY month;

-- 9. 30 天活跃用户(连续 30 天有订单)
-- 简化版:30 天内下过 ≥ 2 单的用户
SELECT
    COUNT(*) AS active_user_count
FROM (
    SELECT user_id
    FROM dwd_orders
    WHERE is_valid_order = 1
      AND order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    GROUP BY user_id
    HAVING COUNT(*) >= 2
) t;

-- 10. 商品销售 Top 10
SELECT
    product_id, product_name, category, brand,
    SUM(quantity) AS total_qty,
    SUM(amount) AS total_sales
FROM dwd_order_items
WHERE is_valid_order = 1
GROUP BY product_id, product_name, category, brand
ORDER BY total_sales DESC
LIMIT 10;
