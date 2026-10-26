{{ config(materialized='table') }}
select
  enrollment_id, student_id, campaign_id, course_id,
  enrollment_date, enrollment_status, list_price_vnd, discount_vnd,
  amount_paid_vnd,
  case when enrollment_status in ('Cancelled', 'Refunded') then 0 else amount_paid_vnd end
    as recognized_revenue_vnd
from {{ ref('stg_enrollments') }}
