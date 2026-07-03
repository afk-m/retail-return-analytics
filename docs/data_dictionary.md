# Data Dictionary

This document describes the main tables and dbt models in the Retail Returns Analytics Warehouse. Please note that (as stated in the project decisions) the project uses synthetic data only, and is intended for portfolio-scale analytics engineering practice.

## Layer Summary

| Layer | Description |
| --- | --- |
| RAW | Generated CSV data loaded into Snowflake with minimal changes. |
| STAGING | Cleaned and standardized dbt views, one per raw table. |
| INTERMEDIATE | Enriched and joined dbt models used to prepare business logic. |
| MARTS | Final business-facing tables for reporting and dashboard use. |

## RAW Tables

| Table Name | Layer | Grain | Purpose | Key Columns | Business Use |
| --- | --- | --- | --- | --- | --- |
| `SALES_RAW` | RAW | One row per sale line item | Stores the original generated sales CSV data loaded into Snowflake. | `sale_id`, `transaction_id`, `sale_date`, `store_id`, `customer_id`, `employee_id`, `product_id`, `quantity`, `sale_amount` | Base sales activity for revenue, product, store, customer, and return-rate analysis. |
| `RETURNS_RAW` | RAW | One row per return event | Stores the original generated returns CSV data loaded into Snowflake. | `return_id`, `sale_id`, `return_date`, `store_id`, `customer_id`, `employee_id`, `product_id`, `return_amount`, `return_reason`, `policy_exception_flag` | Base return activity for return reasons, policy exceptions, refund value, and return timing. |
| `PRODUCTS_RAW` | RAW | One row per product | Stores generated product attributes. | `product_id`, `product_name`, `product_category`, `product_subcategory`, `brand`, `unit_price`, `cost`, `active_flag` | Product grouping and product-level return analysis. |
| `STORES_RAW` | RAW | One row per store | Stores generated store attributes. | `store_id`, `store_name`, `city`, `province`, `region`, `store_type`, `open_date` | Store and regional return comparison. |
| `CUSTOMERS_RAW` | RAW | One row per synthetic customer | Stores non-identifying customer attributes. | `customer_id`, `loyalty_tier`, `signup_date`, `city`, `province` | Loyalty-tier and customer-segment analysis without private customer data. |
| `EMPLOYEES_RAW` | RAW | One row per synthetic employee | Stores non-identifying employee attributes. | `employee_id`, `store_id`, `role`, `hire_date`, `active_flag` | Employee return processing analysis without private employee data. |

Raw tables also include load metadata:

- `loaded_at`: Snowflake load timestamp
- `source_file`: staged file name captured during `COPY INTO`

## STAGING Models

| Model Name | Layer | Grain | Purpose | Key Columns | Business Use |
| --- | --- | --- | --- | --- | --- |
| `STG_SALES` | STAGING | One row per sale line item | Standardizes sales fields from `SALES_RAW`. | `sale_id`, `transaction_id`, `sale_date`, `store_id`, `customer_id`, `employee_id`, `product_id`, `quantity`, `sale_amount`, `payment_method`, `sales_channel` | Clean source for sales metrics and sales-to-returns joins. |
| `STG_RETURNS` | STAGING | One row per return event | Standardizes returns fields from `RETURNS_RAW`. | `return_id`, `sale_id`, `return_date`, `store_id`, `customer_id`, `employee_id`, `product_id`, `return_amount`, `return_reason`, `return_channel` | Clean source for return metrics, return reasons, and policy exception logic. |
| `STG_PRODUCTS` | STAGING | One row per product | Standardizes product attributes. | `product_id`, `product_name`, `product_category`, `product_subcategory`, `brand`, `unit_price`, `cost` | Product-level reporting and return-rate grouping. |
| `STG_STORES` | STAGING | One row per store | Standardizes store attributes. | `store_id`, `store_name`, `city`, `province`, `region`, `store_type` | Store, region, and store-type analysis. |
| `STG_CUSTOMERS` | STAGING | One row per synthetic customer | Standardizes non-identifying customer attributes. | `customer_id`, `loyalty_tier`, `signup_date`, `city`, `province` | Loyalty-tier analysis and customer-context joins. |
| `STG_EMPLOYEES` | STAGING | One row per synthetic employee | Standardizes non-identifying employee attributes. | `employee_id`, `store_id`, `role`, `hire_date`, `active_flag` | Employee role and return processing analysis. |

Common staging logic:

- Trims identifiers and text fields
- Lowercases categorical values where useful
- Uppercases province codes
- Casts dates, timestamps, numbers, and booleans
- Preserves one row per original record
- Overall, cleaning and standardizing for the final two layers

## INTERMEDIATE Models

| Model Name | Layer | Grain | Purpose | Key Columns | Business Use |
| --- | --- | --- | --- | --- | --- |
| `INT_SALES_ENRICHED` | INTERMEDIATE | One row per sale line item | Joins sales to product, store, customer, and employee context. | `sale_id`, `transaction_id`, `sale_date`, `product_id`, `store_id`, `customer_id`, `employee_id`, `gross_sale_amount`, `net_sale_amount`, `discount_rate` | Reusable enriched sales model for sales trends, product sales, store sales, and revenue metrics. |
| `INT_RETURNS_ENRICHED` | INTERMEDIATE | One row per return event | Joins returns to sale dates and dimensional context. | `return_id`, `sale_id`, `return_date`, `product_id`, `store_id`, `customer_id`, `employee_id`, `days_until_return`, `late_return_flag`, `no_receipt_flag`, `damaged_or_defective_flag`, `high_value_return_flag` | Reusable enriched returns model for policy exceptions, return timing, return reason, and return value analysis. |
| `INT_SALES_RETURNS_JOINED` | INTERMEDIATE | One row per sale line item with aggregated return fields | Joins sales to returns without duplicating sale rows. | `sale_id`, `product_id`, `store_id`, `customer_id`, `units_sold`, `units_returned`, `return_count`, `return_amount`, `returned_flag`, `unit_return_rate` | Foundation for return-rate marts by product, store, and other dimensions. |

## MARTS

| Table Name | Layer | Grain | Purpose | Key Columns | Business Use |
| --- | --- | --- | --- | --- | --- |
| `MART_DAILY_SALES_RETURNS_SUMMARY` | MARTS | One row per sale or return calendar date | Summarizes daily sales, returns, return rate, and net revenue after returns. | `calendar_date`, `total_sales`, `total_sales_amount`, `total_returns`, `total_return_amount`, `return_rate`, `net_revenue_after_returns` | Tracks how sales, returns, and net revenue change over time. |
| `MART_RETURN_RATE_BY_PRODUCT` | MARTS | One row per product | Calculates product-level sales, returns, return rate, high-return flag, and top return reason. | `product_id`, `product_name`, `product_category`, `total_units_sold`, `total_units_returned`, `return_rate`, `high_return_product_flag`, `top_return_reason` | Identifies products with high return rates or high refund value. |
| `MART_RETURN_RATE_BY_STORE` | MARTS | One row per store | Calculates store-level return rate, no-receipt return rate, and policy exception rate. | `store_id`, `store_name`, `store_city`, `store_region`, `total_sales`, `total_returns`, `return_rate`, `no_receipt_return_rate`, `policy_exception_rate` | Compares stores and regions for unusual return behavior. |
| `MART_RETURN_REASON_SUMMARY` | MARTS | One row per return reason | Summarizes return counts, return amount, percent of returns, and average return amount by reason. | `return_reason`, `total_returns`, `total_return_amount`, `percent_of_returns`, `average_return_amount` | Explains why items are being returned and which reasons drive the most value. |
| `MART_RETURN_POLICY_EXCEPTIONS` | MARTS | One row per unusual or policy-exception return | Filters to late, no-receipt, damaged or defective, high-value, or policy-flagged returns. | `return_id`, `sale_id`, `return_date`, `store_id`, `employee_id`, `product_id`, `return_amount`, `exception_reason` | Supports review of returns that may break normal policy rules. |
| `MART_EMPLOYEE_RETURN_ACTIVITY` | MARTS | One row per employee | Summarizes return processing activity by employee. | `employee_id`, `store_id`, `employee_role`, `total_returns_processed`, `policy_exception_returns_processed`, `no_receipt_returns_processed`, `unusual_return_activity_flag` | Identifies employees processing unusually high return volume or policy-exception returns. |

## Data Quality Notes

- dbt schema tests check uniqueness, not-null constraints, accepted values, and relationships
- Singular dbt tests check that key raw, staging, and mart tables are not empty
- Non-empty checks are included because many column-level dbt tests can pass when a table has zero rows
- Raw tables intentionally avoid heavy cleaning so later layers can clearly show transformation logic

