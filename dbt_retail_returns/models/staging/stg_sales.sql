-- Standardize raw sales line items without changing the source grain.
with source as (

    select * from {{ source('raw', 'sales_raw') }}

),

staged as (

    select
        trim(sale_id) as sale_id,
        trim(transaction_id) as transaction_id,
        cast(sale_date as date) as sale_date,
        trim(store_id) as store_id,
        trim(customer_id) as customer_id,
        trim(employee_id) as employee_id,
        trim(product_id) as product_id,
        cast(quantity as number(10, 0)) as quantity,
        cast(unit_price as number(10, 2)) as unit_price,
        cast(discount_amount as number(10, 2)) as discount_amount,
        cast(sale_amount as number(10, 2)) as sale_amount,
        lower(trim(payment_method)) as payment_method,
        lower(trim(sales_channel)) as sales_channel,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        trim(source_file) as source_file
    from source

)

select * from staged
