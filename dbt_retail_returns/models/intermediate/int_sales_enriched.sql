-- Enrich sales with dimensional context while keeping one row per sale line.
with sales as (

    select * from {{ ref('stg_sales') }}

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
        sales.sale_id,
        sales.transaction_id,
        sales.sale_date,
        sales.store_id,
        sales.customer_id,
        sales.employee_id,
        sales.product_id,
        sales.quantity,
        sales.unit_price,
        sales.discount_amount,
        sales.sale_amount,
        sales.payment_method,
        sales.sales_channel,
        products.product_name,
        products.product_category,
        products.product_subcategory,
        products.brand,
        products.cost as product_cost,
        products.active_flag as product_active_flag,
        stores.store_name,
        stores.city as store_city,
        stores.province as store_province,
        stores.region as store_region,
        stores.store_type,
        customers.loyalty_tier as customer_loyalty_tier,
        employees.role as employee_role,
        cast(sales.unit_price * sales.quantity as number(12, 2)) as gross_sale_amount,
        cast(sales.sale_amount as number(12, 2)) as net_sale_amount,
        cast(
            sales.discount_amount / nullif(sales.unit_price * sales.quantity, 0)
            as number(10, 4)
        ) as discount_rate,
        sales.loaded_at,
        sales.source_file
    from sales
    left join products
        on sales.product_id = products.product_id
    left join stores
        on sales.store_id = stores.store_id
    left join customers
        on sales.customer_id = customers.customer_id
    left join employees
        on sales.employee_id = employees.employee_id

)

select * from enriched

