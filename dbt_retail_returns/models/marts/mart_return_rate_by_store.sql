-- Store-level sales and returns performance.
with stores as (

    select * from {{ ref('stg_stores') }}

),

sales as (

    select
        store_id,
        count(*) as total_sales,
        sum(net_sale_amount) as total_sales_amount
    from {{ ref('int_sales_enriched') }}
    group by store_id

),

returns as (

    select
        store_id,
        count(*) as total_returns,
        sum(return_amount) as total_return_amount,
        sum(case when no_receipt_flag then 1 else 0 end) as no_receipt_returns,
        sum(case when policy_exception_flag then 1 else 0 end) as policy_exception_returns
    from {{ ref('int_returns_enriched') }}
    group by store_id

),

final as (

    select
        stores.store_id,
        stores.store_name,
        stores.city as store_city,
        stores.province as store_province,
        stores.region as store_region,
        stores.store_type,
        coalesce(sales.total_sales, 0) as total_sales,
        coalesce(sales.total_sales_amount, 0) as total_sales_amount,
        coalesce(returns.total_returns, 0) as total_returns,
        coalesce(returns.total_return_amount, 0) as total_return_amount,
        cast(coalesce(returns.total_returns, 0) / nullif(sales.total_sales, 0) as number(10, 4)) as return_rate,
        cast(coalesce(returns.no_receipt_returns, 0) / nullif(returns.total_returns, 0) as number(10, 4)) as no_receipt_return_rate,
        cast(coalesce(returns.policy_exception_returns, 0) / nullif(returns.total_returns, 0) as number(10, 4)) as policy_exception_rate
    from stores
    left join sales
        on stores.store_id = sales.store_id
    left join returns
        on stores.store_id = returns.store_id

)

select
    store_id,
    store_name,
    store_city,
    store_province,
    store_region,
    store_type,
    total_sales,
    total_sales_amount,
    total_returns,
    total_return_amount,
    coalesce(return_rate, 0) as return_rate,
    coalesce(no_receipt_return_rate, 0) as no_receipt_return_rate,
    coalesce(policy_exception_rate, 0) as policy_exception_rate
from final

