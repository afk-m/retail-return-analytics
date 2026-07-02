-- Standardize raw store records without changing the source grain.
with source as (

    select * from {{ source('raw', 'stores_raw') }}

),

staged as (

    select
        trim(store_id) as store_id,
        trim(store_name) as store_name,
        trim(city) as city,
        upper(trim(province)) as province,
        trim(region) as region,
        lower(trim(store_type)) as store_type,
        cast(open_date as date) as open_date,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        trim(source_file) as source_file
    from source

)

select * from staged
