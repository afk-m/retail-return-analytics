with row_count as (

    select count(*) as records_loaded
    from {{ source('raw', 'sales_raw') }}

)

select
    'RAW.SALES_RAW' as table_name,
    records_loaded
from row_count
where records_loaded = 0

