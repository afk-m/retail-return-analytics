-- One row per return that appears unusual or falls outside normal policy.
with returns as (

    select * from {{ ref('int_returns_enriched') }}

),

exceptions as (

    select
        return_id,
        sale_id,
        transaction_id,
        sale_date,
        return_date,
        store_id,
        store_name,
        store_city,
        store_region,
        customer_id,
        customer_loyalty_tier,
        employee_id,
        employee_role,
        product_id,
        product_name,
        product_category,
        product_subcategory,
        return_quantity,
        return_amount,
        return_reason,
        return_channel,
        refund_method,
        receipt_present,
        item_condition,
        days_until_return,
        late_return_flag,
        no_receipt_flag,
        damaged_or_defective_flag,
        high_value_return_flag,
        policy_exception_flag,
        array_to_string(
            array_construct_compact(
                iff(late_return_flag, 'late_return', null),
                iff(no_receipt_flag, 'no_receipt', null),
                iff(damaged_or_defective_flag, 'damaged_or_defective', null),
                iff(high_value_return_flag, 'high_value_return', null),
                iff(
                    policy_exception_flag
                    and not (
                        late_return_flag
                        or no_receipt_flag
                        or damaged_or_defective_flag
                        or high_value_return_flag
                    ),
                    'source_policy_exception',
                    null
                )
            ),
            ', '
        ) as exception_reason
    from returns
    where
        late_return_flag
        or no_receipt_flag
        or damaged_or_defective_flag
        or high_value_return_flag
        or policy_exception_flag

)

select * from exceptions

