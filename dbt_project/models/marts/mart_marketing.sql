{{ config(materialized='table') }}
select
  c.campaign_id, c.campaign_name, c.channel,
  count(distinct l.lead_id) as total_leads,
  count(distinct if(l.lead_status = 'Converted', l.lead_id, null)) as converted_leads,
  safe_divide(count(distinct if(l.lead_status = 'Converted', l.lead_id, null)),
              count(distinct l.lead_id)) as lead_conversion_rate
from {{ source('bronze', 'campaigns') }} c
left join {{ ref('stg_leads') }} l using (campaign_id)
group by 1,2,3
