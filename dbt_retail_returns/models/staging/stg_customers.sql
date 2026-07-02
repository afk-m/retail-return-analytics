-- Standardize raw non-identifying customer records without changing the source grain.
with source as (

    select * from {{ source('raw', 'customers_raw') }}

),

staged as (

    select
        trim(customer_id) as customer_id,
        lower(trim(loyalty_tier)) as loyalty_tier,
        cast(signup_date as date) as signup_date,
        trim(city) as city,
        upper(trim(province)) as province,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        trim(source_file) as source_file
    from source

)

select * from staged
