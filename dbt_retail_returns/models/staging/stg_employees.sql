-- Standardize raw non-identifying employee records without changing the source grain.
with source as (

    select * from {{ source('raw', 'employees_raw') }}

),

staged as (

    select
        trim(employee_id) as employee_id,
        trim(store_id) as store_id,
        lower(trim(role)) as role,
        cast(hire_date as date) as hire_date,
        cast(active_flag as boolean) as active_flag,
        cast(loaded_at as timestamp_ntz) as loaded_at,
        trim(source_file) as source_file
    from source

)

select * from staged
