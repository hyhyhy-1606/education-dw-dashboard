-- Marketing Data Mart
CREATE OR REPLACE VIEW `data-warehouse-512306.education_dw_gold.mart_marketing` AS
SELECT c.campaign_id, c.campaign_name, c.channel,
       COUNT(DISTINCT l.lead_id) AS total_leads,
       COUNT(DISTINCT IF(l.lead_status='Converted', l.lead_id, NULL)) AS converted_leads,
       SAFE_DIVIDE(COUNT(DISTINCT IF(l.lead_status='Converted', l.lead_id, NULL)),
                   COUNT(DISTINCT l.lead_id)) AS lead_conversion_rate,
       ANY_VALUE(c.marketing_spend) AS marketing_spend_vnd,
       SAFE_DIVIDE(ANY_VALUE(c.marketing_spend), COUNT(DISTINCT l.lead_id)) AS cost_per_lead_vnd
FROM `data-warehouse-512306.education_dw_gold.dim_campaign` c
LEFT JOIN `data-warehouse-512306.education_dw_gold.fact_lead` l USING (campaign_id)
GROUP BY c.campaign_id, c.campaign_name, c.channel;

-- Enrollment & Revenue Data Mart
CREATE OR REPLACE VIEW `data-warehouse-512306.education_dw_gold.mart_enrollment_revenue` AS
SELECT c.course_name, e.enrollment_status,
       COUNT(DISTINCT e.enrollment_id) AS enrollments,
       SUM(e.recognized_revenue_vnd) AS recognized_revenue_vnd,
       SUM(e.discount_vnd) AS discounts_vnd
FROM `data-warehouse-512306.education_dw_gold.fact_enrollment` e
JOIN `data-warehouse-512306.education_dw_gold.dim_course` c USING (course_id)
GROUP BY c.course_name, e.enrollment_status;

-- Learning Data Mart
CREATE OR REPLACE VIEW `data-warehouse-512306.education_dw_gold.mart_learning` AS
SELECT c.course_name,
       COUNTIF(l.attendance_status='Present') AS present_sessions,
       COUNT(*) AS total_sessions,
       SAFE_DIVIDE(COUNTIF(l.attendance_status='Present'), COUNT(*)) AS attendance_rate,
       AVG(l.assessment_score) AS average_assessment_score,
       AVG(l.progress_percent) AS average_progress_percent
FROM `data-warehouse-512306.education_dw_gold.fact_learning` l
JOIN `data-warehouse-512306.education_dw_gold.dim_course` c USING (course_id)
GROUP BY c.course_name;
