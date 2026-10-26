-- Logical Star Schema for the Gold layer (BigQuery Standard SQL)
-- Project: data-warehouse-512306, Dataset Source: education_dw, Target: education_dw_gold
-- Dimensions
CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.dim_date` AS
SELECT
  CAST(FORMAT_DATE('%Y%m%d', d) AS INT64) AS date_key,
  d AS full_date,
  EXTRACT(DAY FROM d) AS day_of_month,
  EXTRACT(MONTH FROM d) AS month_number,
  FORMAT_DATE('%B', d) AS month_name,
  EXTRACT(QUARTER FROM d) AS quarter_number,
  EXTRACT(YEAR FROM d) AS year_number
FROM UNNEST(GENERATE_DATE_ARRAY(DATE '2025-01-01', DATE '2027-12-31')) AS d;

CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.dim_student` AS
SELECT
  student_id,
  COALESCE(gender, 'Chưa xác định') AS gender,
  SAFE_CAST(date_of_birth AS DATE) AS date_of_birth,
  CAST(grade AS STRING) AS grade,
  school_id,
  district
FROM `data-warehouse-512306.education_dw.students_clean`;

CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.dim_course` AS
SELECT course_id, course_name, subject_group, course_level, standard_fee_vnd
FROM `data-warehouse-512306.education_dw.courses_clean`;

CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.dim_campaign` AS
SELECT campaign_id, campaign_name, channel, SAFE_CAST(start_date AS DATE) AS start_date,
       SAFE_CAST(end_date AS DATE) AS end_date, marketing_spend, impressions, clicks
FROM `data-warehouse-512306.education_dw.campaigns_clean`;

-- Fact grains:
-- fact_lead: one row per lead_id
-- fact_enrollment: one row per enrollment_id
-- fact_learning: one row per learning_record_id (session grain)
-- fact_career_guidance: one row per guidance_id
CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.fact_lead` AS
SELECT l.lead_id, l.student_id, l.campaign_id,
       SAFE_CAST(l.lead_created_date AS DATE) AS lead_date,
       l.lead_source, l.lead_status, l.contact_attempts, l.first_response_hours,
       IF(l.lead_status = 'Converted', 1, 0) AS is_converted
FROM `data-warehouse-512306.education_dw.leads_clean` l;

CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.fact_enrollment` AS
SELECT e.enrollment_id, e.student_id, e.campaign_id, e.course_id,
       SAFE_CAST(e.enrollment_date AS DATE) AS enrollment_date,
       e.enrollment_status, e.list_price_vnd, e.discount_vnd, e.amount_paid_vnd,
       IF(e.enrollment_status IN ('Cancelled','Refunded'), 0, e.amount_paid_vnd) AS recognized_revenue_vnd
FROM `data-warehouse-512306.education_dw.enrollments_clean` e;

CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.fact_learning` AS
SELECT learning_record_id, enrollment_id, student_id, course_id,
       SAFE_CAST(session_date AS DATE) AS session_date, session_number,
       attendance_status, assessment_score, progress_percent
FROM `data-warehouse-512306.education_dw.learning_records_clean`;

CREATE OR REPLACE TABLE `data-warehouse-512306.education_dw_gold.fact_career_guidance` AS
SELECT guidance_id, student_id, SAFE_CAST(guidance_date AS DATE) AS guidance_date,
       guidance_type, advisor_id, outcome, satisfaction_score
FROM `data-warehouse-512306.education_dw.career_guidance_clean`;
