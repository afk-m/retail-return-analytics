-- Return reason distribution for understanding why products come back.
with returns as (

    select * from {{ ref('int_returns_enriched') }}

),

reason_metrics as (

    select
        return_reason,
        count(*) as total_returns,
        sum(return_amount) as total_return_amount,
        avg(return_amount) as average_return_amount
    from returns
    group by return_reason

),

final as (

    select
        return_reason,
        total_returns,
        total_return_amount,
        cast(total_returns / nullif(sum(total_returns) over (), 0) as number(10, 4)) as percent_of_returns,
        average_return_amount
    from reason_metrics

)

select
    return_reason,
    total_returns,
    total_return_amount,
    coalesce(percent_of_returns, 0) as percent_of_returns,
    average_return_amount
from final

