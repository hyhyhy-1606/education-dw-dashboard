{{ config(materialized='table') }}
with dates as (
  select d as full_date
  from unnest(generate_date_array(date '2025-01-01', date '2027-12-31')) d
)
select
  cast(format_date('%Y%m%d', full_date) as int64) as date_key,
  full_date,
  extract(day from full_date) as day_of_month,
  extract(month from full_date) as month_number,
  format_date('%B', full_date) as month_name,
  extract(quarter from full_date) as quarter_number,
  extract(year from full_date) as year_number
from dates
