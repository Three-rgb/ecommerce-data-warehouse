-- ============================================
-- ODS 层常用查询模板
-- 直接在 DuckDB CLI 跑,或在 Python 里 con.execute()
-- ============================================

-- 1. 看每张表的行数(数据健康度检查)
SELECT 'ods_users' AS table_name, COUNT(*) AS row_count FROM ods_users
UNION ALL
SELECT 'ods_products', COUNT(*) FROM ods_products
UNION ALL
SELECT 'ods_orders', COUNT(*) FROM ods_orders
UNION ALL
SELECT 'ods_order_items', COUNT(*) FROM ods_order_items;

-- 2. 看用户基础信息
SELECT * FROM ods_users LIMIT 10;

-- 3. 订单状态分布
SELECT status, COUNT(*) AS cnt, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(), 2) AS pct
FROM ods_orders
GROUP BY status
ORDER BY cnt DESC;

-- 4. 看时间范围
SELECT
    MIN(create_time) AS earliest_order,
    MAX(create_time) AS latest_order,
    DATEDIFF('day', MIN(create_time), MAX(create_time)) AS day_span
FROM ods_orders;

-- 5. 检查空值(数据质量)
SELECT
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE user_id IS NULL) AS null_user_id,
    COUNT(*) FILTER (WHERE total_amount IS NULL) AS null_amount,
    COUNT(*) FILTER (WHERE total_amount <= 0) AS invalid_amount
FROM ods_orders;

-- 6. 看订单金额分布
SELECT
    MIN(total_amount) AS min_amt,
    AVG(total_amount) AS avg_amt,
    MEDIAN(total_amount) AS median_amt,
    MAX(total_amount) AS max_amt
FROM ods_orders
WHERE status IN ('paid', 'shipped', 'received');

-- 7. 订单最多的用户 Top 10
SELECT user_id, COUNT(*) AS order_count, SUM(total_amount) AS total_spent
FROM ods_orders
WHERE status IN ('paid', 'shipped', 'received')
GROUP BY user_id
ORDER BY order_count DESC
LIMIT 10;

-- 8. 各品类订单数(需要 JOIN ods_order_items 和 ods_products)
SELECT
    p.category,
    COUNT(DISTINCT oi.order_id) AS order_count,
    SUM(oi.amount) AS gmv
FROM ods_order_items oi
JOIN ods_products p ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY gmv DESC;

-- 9. 按月统计订单量(注意 DuckDB 用 DATE_TRUNC)
SELECT
    DATE_TRUNC('month', create_time) AS month,
    COUNT(*) AS order_count,
    SUM(total_amount) AS gmv
FROM ods_orders
WHERE status IN ('paid', 'shipped', 'received')
GROUP BY month
ORDER BY month;

-- 10. 复购用户(下过 ≥ 2 单的)
SELECT user_id, COUNT(*) AS order_count
FROM ods_orders
WHERE status IN ('paid', 'shipped', 'received')
GROUP BY user_id
HAVING COUNT(*) >= 2
ORDER BY order_count DESC
LIMIT 20;
