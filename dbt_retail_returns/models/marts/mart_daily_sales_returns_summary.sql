-- Daily operating summary across sale dates and return dates.
with sales_by_day as (

    select
        sale_date as calendar_date,
        count(*) as total_sales,
        sum(net_sale_amount) as total_sales_amount
    from {{ ref('int_sales_enriched') }}
    group by sale_date

),

returns_by_day as (

    select
        return_date as calendar_date,
        count(*) as total_returns,
        sum(return_amount) as total_return_amount
    from {{ ref('int_returns_enriched') }}
    group by return_date

),

calendar_days as (

    select calendar_date from sales_by_day
    union
    select calendar_date from returns_by_day

),

final as (

    select
        calendar_days.calendar_date,
        coalesce(sales_by_day.total_sales, 0) as total_sales,
        coalesce(sales_by_day.total_sales_amount, 0) as total_sales_amount,
        coalesce(returns_by_day.total_returns, 0) as total_returns,
        coalesce(returns_by_day.total_return_amount, 0) as total_return_amount,
        cast(
            coalesce(returns_by_day.total_returns, 0) / nullif(sales_by_day.total_sales, 0)
            as number(10, 4)
        ) as return_rate,
        coalesce(sales_by_day.total_sales_amount, 0)
            - coalesce(returns_by_day.total_return_amount, 0) as net_revenue_after_returns
    from calendar_days
    left join sales_by_day
        on calendar_days.calendar_date = sales_by_day.calendar_date
    left join returns_by_day
        on calendar_days.calendar_date = returns_by_day.calendar_date

)

select
    calendar_date,
    total_sales,
    total_sales_amount,
    total_returns,
    total_return_amount,
    coalesce(return_rate, 0) as return_rate,
    net_revenue_after_returns
from final

