-- ============================================
-- RFM 客户分层(面试必考)⭐⭐⭐
-- 8 类客户的识别和应用
-- ============================================

-- 第 1 题:8 类客户分布
SELECT
    rfm_segment,
    COUNT(*) AS user_count,
    ROUND(AVG(total_amount), 2) AS avg_amount,
    ROUND(AVG(valid_orders), 2) AS avg_orders
FROM dws_user_summary
WHERE valid_orders > 0
GROUP BY rfm_segment
ORDER BY user_count DESC;


-- 第 2 题:重要价值客户(高 R + 高 F + 高 M)详情
SELECT
    user_id, username, city, user_level,
    valid_orders, total_amount,
    days_since_last,
    r_score, f_score, m_score, rfm_score
FROM dws_user_summary
WHERE rfm_segment = '重要价值客户'
ORDER BY total_amount DESC
LIMIT 20;


-- 第 3 题:流失客户识别(低 R + 低 F + 高 M)
-- 这些用户:曾经消费高,但最近没来,需要挽留
SELECT
    user_id, username, city,
    valid_orders, total_amount,
    days_since_last AS days_inactive,
    r_score, f_score, m_score
FROM dws_user_summary
WHERE rfm_segment = '重要挽留客户' OR rfm_segment = '流失客户'
ORDER BY total_amount DESC
LIMIT 30;


-- 第 4 题:营销策略建议(根据分层)
SELECT
    rfm_segment,
    COUNT(*) AS user_count,
    CASE
        WHEN rfm_segment = '重要价值客户' THEN 'VIP 专属服务 + 新品优先体验'
        WHEN rfm_segment = '重要发展客户' THEN '推送新客优惠券,刺激复购'
        WHEN rfm_segment = '重要保持客户' THEN '定期唤醒邮件,防流失'
        WHEN rfm_segment = '重要挽留客户' THEN '大额优惠券 + 客服主动联系'
        WHEN rfm_segment = '一般价值客户' THEN '保持现状,偶尔推送'
        WHEN rfm_segment = '一般发展客户' THEN '新客礼包 + 引导探索'
        WHEN rfm_segment = '一般保持客户' THEN '标准推送'
        ELSE '不投入营销资源'
    END AS marketing_strategy
FROM dws_user_summary
WHERE valid_orders > 0
GROUP BY rfm_segment
ORDER BY user_count DESC;


-- 第 5 题:RFM 三维度的 5 档分布
SELECT
    r_score, f_score, m_score,
    COUNT(*) AS user_count
FROM dws_user_summary
WHERE valid_orders > 0
GROUP BY r_score, f_score, m_score
ORDER BY m_score DESC, f_score DESC, r_score DESC
LIMIT 30;


-- 第 6 题:客户价值 vs 平均客单价
SELECT
    rfm_segment,
    ROUND(AVG(avg_order_amount), 2) AS avg_aov,
    ROUND(AVG(total_amount / valid_orders), 2) AS calc_aov
FROM dws_user_summary
WHERE valid_orders > 0
GROUP BY rfm_segment
ORDER BY avg_aov DESC;
