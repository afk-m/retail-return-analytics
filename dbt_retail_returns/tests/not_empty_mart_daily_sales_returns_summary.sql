with row_count as (

    select count(*) as records_loaded
    from {{ ref('mart_daily_sales_returns_summary') }}

)

select
    'MARTS.MART_DAILY_SALES_RETURNS_SUMMARY' as table_name,
    records_loaded
from row_count
where records_loaded = 0

