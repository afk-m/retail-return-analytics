-- Enrich returns with sale dates and dimensional context while keeping one row per return.
with returns as (

    select * from {{ ref('stg_returns') }}

),

sales as (

    select
        sale_id,
        sale_date
    from {{ ref('stg_sales') }}

),

products as (

    select * from {{ ref('stg_products') }}

),

stores as (

    select * from {{ ref('stg_stores') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

),

employees as (

    select * from {{ ref('stg_employees') }}

),

enriched as (

    select
        returns.return_id,
        returns.sale_id,
        returns.transaction_id,
        sales.sale_date,
        returns.return_date,
        returns.store_id,
        returns.customer_id,
        returns.employee_id,
        returns.product_id,
        returns.return_quantity,
        returns.return_amount,
        returns.return_reason,
        returns.return_channel,
        returns.refund_method,
        returns.receipt_present,
        returns.item_condition,
        coalesce(returns.policy_exception_flag, false) as policy_exception_flag,
        products.product_name,
        products.product_category,
        products.product_subcategory,
        products.brand,
        stores.store_name,
        stores.city as store_city,
        stores.province as store_province,
        stores.region as store_region,
        stores.store_type,
        customers.loyalty_tier as customer_loyalty_tier,
        employees.role as employee_role,
        datediff(day, sales.sale_date, returns.return_date) as days_until_return,
        coalesce(datediff(day, sales.sale_date, returns.return_date) > 30, false) as late_return_flag,
        coalesce(returns.receipt_present = false, false) as no_receipt_flag,
        coalesce(
            returns.item_condition in ('damaged', 'defective')
            or returns.return_reason in ('damaged', 'defective'),
            false
        ) as damaged_or_defective_flag,
        -- High-value returns are defined as returns of 200.00 or more in this portfolio model.
        coalesce(returns.return_amount >= 200.00, false) as high_value_return_flag,
        returns.loaded_at,
        returns.source_file
    from returns
    left join sales
        on returns.sale_id = sales.sale_id
    left join products
        on returns.product_id = products.product_id
    left join stores
        on returns.store_id = stores.store_id
    left join customers
        on returns.customer_id = customers.customer_id
    left join employees
        on returns.employee_id = employees.employee_id

)

select * from enriched
