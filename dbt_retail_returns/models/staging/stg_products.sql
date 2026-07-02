-- Standardize raw product records without changing the source grain.
with source as (

    select * from {{ source('raw', 'products_raw') }}

),

staged as (

    select
        trim(product_id) as product_id,
        trim(product_name) as product_name,
        lower(trim(product_category)) as product_category,
        lower(trim(product_subcategory)) as product_subcategory,
        trim(brand) as brand,
        cast(unit_price as number(10, 2)) as unit_price,
        cast(cost as number(10, 2)) as cost,
        cast(active_flag as boolean) as active_flag,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        trim(source_file) as source_file
    from source

)

select * from staged
