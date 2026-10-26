{{ config(materialized='view', schema='silver') }}
select
  enrollment_id, student_id, nullif(trim(lead_id), '') as lead_id,
  campaign_id, course_id, trim(course_name) as course_name,
  safe_cast(enrollment_date as date) as enrollment_date,
  initcap(trim(enrollment_status)) as enrollment_status,
  greatest(safe_cast(list_price_vnd as numeric), 0) as list_price_vnd,
  greatest(safe_cast(discount_vnd as numeric), 0) as discount_vnd,
  greatest(safe_cast(amount_paid_vnd as numeric), 0) as amount_paid_vnd
from {{ source('bronze', 'enrollments') }}
qualify row_number() over (partition by enrollment_id order by enrollment_date desc) = 1
