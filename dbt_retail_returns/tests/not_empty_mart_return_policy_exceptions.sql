with row_count as (

    select count(*) as records_loaded
    from {{ ref('mart_return_policy_exceptions') }}

)

select
    'MARTS.MART_RETURN_POLICY_EXCEPTIONS' as table_name,
    records_loaded
from row_count
where records_loaded = 0

