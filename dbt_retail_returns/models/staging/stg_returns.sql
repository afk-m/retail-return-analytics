-- Standardize raw return events without changing the source grain.
with source as (

    select * from {{ source('raw', 'returns_raw') }}

),

staged as (

    select
        trim(return_id) as return_id,
        trim(sale_id) as sale_id,
        trim(transaction_id) as transaction_id,
        cast(return_date as date) as return_date,
        trim(store_id) as store_id,
        trim(customer_id) as customer_id,
        trim(employee_id) as employee_id,
        trim(product_id) as product_id,
        cast(return_quantity as number(10, 0)) as return_quantity,
        cast(return_amount as number(10, 2)) as return_amount,
        lower(trim(return_reason)) as return_reason,
        lower(trim(return_channel)) as return_channel,
        lower(trim(refund_method)) as refund_method,
        cast(receipt_present as boolean) as receipt_present,
        lower(trim(item_condition)) as item_condition,
        cast(policy_exception_flag as boolean) as policy_exception_flag,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        trim(source_file) as source_file
    from source

)

select * from staged
