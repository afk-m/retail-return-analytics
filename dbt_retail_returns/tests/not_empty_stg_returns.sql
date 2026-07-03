with row_count as (

    select count(*) as records_loaded
    from {{ ref('stg_returns') }}

)

select
    'STAGING.STG_RETURNS' as table_name,
    records_loaded
from row_count
where records_loaded = 0

