# Retail Returns Analytics Warehouse

Retail Returns Analytics Warehouse is a portfolio-scale analytics engineering project for understanding retail sales and product returns. It uses synthetic data only and does not include real customer, employee, or private business data, nor is it intended to represent real-life distributions or metrics of a real retail company. It is purely for pipeline construction, schema building and data visualization purposes.

## Business Problem

Retail companies need to understand why products are returned, which products have high return rates, which stores show unusual return patterns, and which returns may break normal policy rules kept in place. Return behavior can affect revenue, inventory planning, customer experience, store operations, and LP (loss prevention).

Working at companies like Shoppers Drug Mart or Winners as a cashier, I could only imagine how this data can be used to make and shape decisions (especially related to product sourcing and loss prevention, which is taken seriously in a department store), but in order for this data to shape decisions, it needs to be transformed and stored properly first. This project focuses on that aspect of data engineering, and a little bit of analysis as well as these things go hand in hand. 

This project models that problem with a small but realistic warehouse:

- Generate synthetic retail sales and returns data
- Load raw CSV files into Snowflake
- Use dbt Core to clean, test, join, and transform the data
- Build business-ready mart tables for common return analysis questions
- Power a Streamlit dashboard from the final mart tables

## What This Project Does

1. Creates synthetic sales, returns, product, store, customer, and employee CSV files with Python
2. Defines a Snowflake database, schemas, raw tables, file format, stage, and `COPY INTO` templates
3. Builds dbt staging models that standardize raw tables
4. Builds dbt intermediate models that enrich and join sales and returns data
5. Builds final mart tables for reporting and dashboard use
6. Adds dbt tests, including non-empty checks for key source and mart tables
7. Provides a Streamlit dashboard using Snowflake mart tables

## Tools Used

- Python
- pandas
- Faker
- Snowflake
- dbt Core
- SQL
- Streamlit
- Plotly
- pytest

## Data Layers

| Layer | Plain-English Purpose |
| --- | --- |
| RAW | Original generated CSV data loaded into Snowflake with minimal changes |
| STAGING | Cleaned and standardized versions of each raw table |
| INTERMEDIATE | Joined and enriched models used to prepare reusable business logic |
| MARTS | Final reporting tables built for business questions and Streamlit dashboard use |

Full flow:

```text
Synthetic CSV generator -> Snowflake RAW -> dbt STAGING -> dbt INTERMEDIATE -> dbt MARTS -> Streamlit dashboard (marts)
```

## Final Mart Tables

- `MART_DAILY_SALES_RETURNS_SUMMARY`
- `MART_RETURN_RATE_BY_PRODUCT`
- `MART_RETURN_RATE_BY_STORE`
- `MART_RETURN_REASON_SUMMARY`
- `MART_RETURN_POLICY_EXCEPTIONS`
- `MART_EMPLOYEE_RETURN_ACTIVITY`

## Business Questions Answered

- Which products are returned the most?
- Which stores have the highest return rates?
- Why are customers returning items?
- Which returns are policy exceptions?
- Which employees are processing unusual return activity?
- How do sales, returns, and net revenue change over time?

## Screenshots

Coming soon! These are just placeholders!

- ![Streamlit overview](http://localhost)
- ![Product returns tab](http://localhost)
- ![Store returns tab](http://localhost)
- ![Policy exceptions tab](http://localhost)
- ![dbt test results](http://localhost)
- ![Snowflake marts schema](http://localhost)

## How to Run

### 1. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

### 2. Install Requirements

```bash
pip install -r requirements.txt
```

### 3. Generate Synthetic Data

```bash
python data_generator/generate_data.py --output-dir data/sample
```

Default row counts:

- 50,000 sales
- 6,000 returns
- 500 products
- 20 stores
- 10,000 customers
- 150 employees

Run the Python generator tests:

```bash
pytest -q
```

### 4. Create Snowflake Database and Raw Tables

In Snowflake Snowsight, open and run the contents of:

- `warehouse/01_create_database.sql`
- `warehouse/02_create_raw_tables.sql`

These scripts create:

- Database: `RETAIL_RETURNS_ANALYTICS`
- Schemas: `RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`, `QA`
- Raw tables
- CSV file format
- Example internal stage

### 5. Load CSVs into Snowflake

Upload the CSV files from `data/sample` to the Snowflake stage, then open and run the contents of `warehouse/03_load_data_template.sql`.

Then you can update the stage paths in the load template if your files are uploaded under a folder or compressed. Do not put credentials in this repository.

### 6. Configure dbt

Create a local dbt profile named `retail_returns` outside this repo, usually in `~/.dbt/profiles.yml` (at least that's what I used). Use environment variables or another secure credential method:

```yaml
retail_returns:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: RETAIL_RETURNS_ANALYTICS
      schema: STAGING
      threads: 4
      client_session_keep_alive: false
```

### 7. Run dbt Models

```bash
cd dbt_retail_returns
dbt debug
dbt run
```

Or you can run by layer:

```bash
dbt run --select staging
dbt run --select intermediate marts
```

### 8. Run dbt Tests

```bash
dbt test
```

The project includes schema tests such as `not_null`, `unique`, `accepted_values`, and `relationships`. It also includes singular non-empty table checks for key raw, staging, and mart tables because dbt `not_null` and `unique` tests can pass on empty tables.

### 9. Run the Streamlit Dashboard

Create a local `.env` file from `.env.example` or export these variables:

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

Run:

```bash
streamlit run dashboard/app.py
```

## Dashboard Sections

| Section | Powered By |
| --- | --- |
| Overview and Daily Trends | `MARTS.MART_DAILY_SALES_RETURNS_SUMMARY` |
| Product Returns | `MARTS.MART_RETURN_RATE_BY_PRODUCT` |
| Store Returns | `MARTS.MART_RETURN_RATE_BY_STORE` |
| Return Reasons | `MARTS.MART_RETURN_REASON_SUMMARY` |
| Policy Exceptions | `MARTS.MART_RETURN_POLICY_EXCEPTIONS` |
| Employee Return Activity | `MARTS.MART_EMPLOYEE_RETURN_ACTIVITY` |

## Documentation

You can consult some handier documentation as well, in case you were curious:

- [Architecture](docs/architecture.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Dashboard Guide](docs/dashboard.md)
- [Project Decisions](docs/project_decisions.md)

## What To Improve Next

- Add scheduled ingestion.
- Add incremental dbt models.
- Add automated alerts for failed data quality checks.
- Deploy the Streamlit dashboard.
- Add role-based access control.
- Add more advanced anomaly detection for unusual return patterns.

## Another Data Privacy Note

As stated before, this project uses synthetic data generated for portfolio purposes. Already-synthetic customer and employee records are intentionally non-identifying and do not include names, emails, phone numbers, or street addresses.
