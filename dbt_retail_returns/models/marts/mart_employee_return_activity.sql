-- Employee-level return processing metrics; unusual activity means >= 2x average return count and at least 5 returns.
with employees as (

    select * from {{ ref('stg_employees') }}

),

returns as (

    select * from {{ ref('int_returns_enriched') }}

),

employee_returns as (

    select
        employee_id,
        count(*) as total_returns_processed,
        sum(return_amount) as total_return_amount_processed,
        sum(case when no_receipt_flag then 1 else 0 end) as no_receipt_returns_processed,
        sum(case when policy_exception_flag then 1 else 0 end) as policy_exception_returns_processed,
        avg(return_amount) as average_return_amount
    from returns
    group by employee_id

),

employee_activity as (

    select
        employees.employee_id,
        employees.store_id,
        employees.role as employee_role,
        employees.hire_date,
        employees.active_flag,
        coalesce(employee_returns.total_returns_processed, 0) as total_returns_processed,
        coalesce(employee_returns.total_return_amount_processed, 0) as total_return_amount_processed,
        coalesce(employee_returns.no_receipt_returns_processed, 0) as no_receipt_returns_processed,
        coalesce(employee_returns.policy_exception_returns_processed, 0) as policy_exception_returns_processed,
        coalesce(employee_returns.average_return_amount, 0) as average_return_amount
    from employees
    left join employee_returns
        on employees.employee_id = employee_returns.employee_id

),

thresholds as (

    select
        avg(total_returns_processed) as average_returns_processed
    from employee_activity

),

final as (

    select
        employee_activity.employee_id,
        employee_activity.store_id,
        employee_activity.employee_role,
        employee_activity.hire_date,
        employee_activity.active_flag,
        employee_activity.total_returns_processed,
        employee_activity.total_return_amount_processed,
        employee_activity.no_receipt_returns_processed,
        employee_activity.policy_exception_returns_processed,
        employee_activity.average_return_amount,
        (
            employee_activity.total_returns_processed >= 5
            and employee_activity.total_returns_processed >= thresholds.average_returns_processed * 2
        ) as unusual_return_activity_flag
    from employee_activity
    cross join thresholds

)

select * from final

