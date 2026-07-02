-- Join sale lines to aggregated returns so each sale remains one row.
with sales as (

    select * from {{ ref('int_sales_enriched') }}

),

returns as (

    select * from {{ ref('int_returns_enriched') }}

),

returns_by_sale as (

    select
        sale_id,
        transaction_id,
        product_id,
        store_id,
        customer_id,
        count(*) as return_count,
        sum(return_quantity) as total_return_quantity,
        sum(return_amount) as total_return_amount,
        min(return_date) as first_return_date,
        max(return_date) as last_return_date,
        max(case when late_return_flag then 1 else 0 end) = 1 as late_return_flag,
        max(case when no_receipt_flag then 1 else 0 end) = 1 as no_receipt_flag,
        max(case when damaged_or_defective_flag then 1 else 0 end) = 1 as damaged_or_defective_flag,
        max(case when high_value_return_flag then 1 else 0 end) = 1 as high_value_return_flag,
        max(case when policy_exception_flag then 1 else 0 end) = 1 as policy_exception_flag
    from returns
    group by
        sale_id,
        transaction_id,
        product_id,
        store_id,
        customer_id

),

joined as (

    select
        sales.sale_id,
        sales.transaction_id,
        sales.sale_date,
        sales.store_id,
        sales.customer_id,
        sales.employee_id,
        sales.product_id,
        sales.quantity as units_sold,
        sales.unit_price,
        sales.discount_amount,
        sales.gross_sale_amount,
        sales.net_sale_amount,
        sales.discount_rate,
        sales.payment_method,
        sales.sales_channel,
        sales.product_name,
        sales.product_category,
        sales.product_subcategory,
        sales.brand,
        sales.store_name,
        sales.store_city,
        sales.store_province,
        sales.store_region,
        sales.store_type,
        sales.customer_loyalty_tier,
        sales.employee_role,
        coalesce(returns_by_sale.return_count, 0) as return_count,
        coalesce(returns_by_sale.total_return_quantity, 0) as units_returned,
        coalesce(returns_by_sale.total_return_amount, 0) as return_amount,
        returns_by_sale.first_return_date,
        returns_by_sale.last_return_date,
        coalesce(returns_by_sale.return_count, 0) > 0 as returned_flag,
        cast(coalesce(returns_by_sale.return_count, 0) as number(10, 0)) as returned_sale_count,
        cast(1 as number(10, 0)) as sale_line_count,
        cast(
            coalesce(returns_by_sale.total_return_quantity, 0) / nullif(sales.quantity, 0)
            as number(10, 4)
        ) as unit_return_rate,
        coalesce(returns_by_sale.late_return_flag, false) as late_return_flag,
        coalesce(returns_by_sale.no_receipt_flag, false) as no_receipt_flag,
        coalesce(returns_by_sale.damaged_or_defective_flag, false) as damaged_or_defective_flag,
        coalesce(returns_by_sale.high_value_return_flag, false) as high_value_return_flag,
        coalesce(returns_by_sale.policy_exception_flag, false) as policy_exception_flag
    from sales
    left join returns_by_sale
        on sales.sale_id = returns_by_sale.sale_id
        and sales.transaction_id = returns_by_sale.transaction_id
        and sales.product_id = returns_by_sale.product_id
        and sales.store_id = returns_by_sale.store_id
        and sales.customer_id = returns_by_sale.customer_id

)

select * from joined

