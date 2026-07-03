with row_count as (

    select count(*) as records_loaded
    from {{ ref('mart_return_rate_by_store') }}

)

select
    'MARTS.MART_RETURN_RATE_BY_STORE' as table_name,
    records_loaded
from row_count
where records_loaded = 0

