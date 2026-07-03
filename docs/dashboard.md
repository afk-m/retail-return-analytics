# Dashboard

The Streamlit dashboard presents the final dbt marts as a simple business-facing retail returns analytics app. It connects to Snowflake using environment variables and queries the `MARTS` schema only.

As stated elsewhere in this documentation, this is a portfolio-scale dashboard. It is designed to explain the value of the warehouse clearly, not to replace a production BI platform- and of course, the synthetic data is not meant to represent the distributions and metrics of real retail data used in the real world.

## Sections

| Section | Business Question Answered | Mart Table Used | Key Metrics Shown |
| --- | --- | --- | --- |
| Overview | What is the overall sales and returns picture? | `MART_DAILY_SALES_RETURNS_SUMMARY` | Total sales, total sales amount, total returns, total return amount, overall return rate, net revenue after returns. |
| Daily Trends | How do sales, returns, and return rate change over time? | `MART_DAILY_SALES_RETURNS_SUMMARY` | Daily sales amount, daily return amount, daily return rate. |
| Product Returns | Which products are driving return risk and refund value? | `MART_RETURN_RATE_BY_PRODUCT` | Top products by return rate, top products by return amount, high-return product table, top return reason. |
| Store Returns | Which stores show higher return rates or unusual return behavior? | `MART_RETURN_RATE_BY_STORE` | Return rate by store, policy exception rate by store, no-receipt return rate by store. |
| Return Reasons | Why are customers returning items? | `MART_RETURN_REASON_SUMMARY` | Total returns by reason, return amount by reason, percent of returns by reason, average return amount. |
| Policy Exceptions | Which returns look unusual or outside normal policy? | `MART_RETURN_POLICY_EXCEPTIONS` | Exception return table, exception reason counts, return reason filter, store filter, exception type filter. |
| Employee Activity | Which employees are processing unusual return activity? | `MART_EMPLOYEE_RETURN_ACTIVITY` | Total returns processed, policy exception returns processed, no-receipt returns processed, average return amount, unusual return activity flag. |

## Environment Variables

The dashboard does not hardcode credentials. It expects these variables:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_ROLE`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_SCHEMA`

For this project:

- `SNOWFLAKE_DATABASE=RETAIL_RETURNS_ANALYTICS`
- `SNOWFLAKE_SCHEMA=MARTS`

Use `.env.example` as a template for local development. Do not commit real credentials.

## How to Run

```bash
streamlit run dashboard/app.py
```

## Design Notes

- Query results are cached with Streamlit caching to avoid repeatedly hitting Snowflake while navigating the app
- The dashboard reads from marts only, not raw or staging tables
- Plotly is used for simple interactive charts
- Filters are intentionally light so the project stays easy to understand during review

