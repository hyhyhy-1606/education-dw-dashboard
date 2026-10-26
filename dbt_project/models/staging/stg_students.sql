{{ config(materialized='view', schema='silver') }}
select
  student_id,
  coalesce(nullif(trim(gender), ''), 'Chưa xác định') as gender,
  safe_cast(date_of_birth as date) as date_of_birth,
  regexp_extract(cast(grade as string), r'(10|11|12)') as grade,
  school_id,
  initcap(trim(district)) as district,
  safe_cast(created_at as date) as created_at
from {{ source('bronze', 'students') }}
qualify row_number() over (partition by student_id order by created_at desc) = 1
