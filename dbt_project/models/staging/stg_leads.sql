{{ config(materialized='view', schema='silver') }}
select
  lead_id, student_id, campaign_id,
  safe_cast(lead_created_date as date) as lead_created_date,
  trim(lead_source) as lead_source,
  initcap(trim(lead_status)) as lead_status,
  greatest(safe_cast(contact_attempts as int64), 0) as contact_attempts,
  safe_cast(first_response_hours as numeric) as first_response_hours
from {{ source('bronze', 'leads') }}
qualify row_number() over (partition by lead_id order by lead_created_date desc) = 1
