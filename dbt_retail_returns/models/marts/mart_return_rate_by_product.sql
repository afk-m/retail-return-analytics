-- Product return performance; high-return products are >= 20% unit return rate with at least 10 units sold.
with products as (

    select * from {{ ref('stg_products') }}

),

sales_returns as (

    select * from {{ ref('int_sales_returns_joined') }}

),

product_metrics as (

    select
        product_id,
        sum(units_sold) as total_units_sold,
        sum(net_sale_amount) as total_sales_amount,
        sum(units_returned) as total_units_returned,
        sum(return_amount) as total_return_amount
    from sales_returns
    group by product_id

),

return_reasons as (

    select
        product_id,
        return_reason,
        count(*) as reason_return_count,
        sum(return_amount) as reason_return_amount
    from {{ ref('int_returns_enriched') }}
    group by product_id, return_reason

),

ranked_return_reasons as (

    select
        product_id,
        return_reason,
        row_number() over (
            partition by product_id
            order by reason_return_count desc, reason_return_amount desc, return_reason
        ) as reason_rank
    from return_reasons

),

final as (

    select
        products.product_id,
        products.product_name,
        products.product_category,
        products.product_subcategory,
        products.brand,
        coalesce(product_metrics.total_units_sold, 0) as total_units_sold,
        coalesce(product_metrics.total_sales_amount, 0) as total_sales_amount,
        coalesce(product_metrics.total_units_returned, 0) as total_units_returned,
        coalesce(product_metrics.total_return_amount, 0) as total_return_amount,
        cast(
            coalesce(product_metrics.total_units_returned, 0)
            / nullif(product_metrics.total_units_sold, 0)
            as number(10, 4)
        ) as return_rate,
        (
            coalesce(product_metrics.total_units_sold, 0) >= 10
            and coalesce(product_metrics.total_units_returned, 0)
                / nullif(product_metrics.total_units_sold, 0) >= 0.20
        ) as high_return_product_flag,
        ranked_return_reasons.return_reason as top_return_reason
    from products
    left join product_metrics
        on products.product_id = product_metrics.product_id
    left join ranked_return_reasons
        on products.product_id = ranked_return_reasons.product_id
        and ranked_return_reasons.reason_rank = 1

)

select
    product_id,
    product_name,
    product_category,
    product_subcategory,
    brand,
    total_units_sold,
    total_sales_amount,
    total_units_returned,
    total_return_amount,
    coalesce(return_rate, 0) as return_rate,
    coalesce(high_return_product_flag, false) as high_return_product_flag,
    top_return_reason
from final

