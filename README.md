# Retail Returns Analytics Warehouse

Portfolio project for generating synthetic retail sales and returns data, then loading it into Snowflake for later dbt transformation and analytics.

This project uses fake data only. It does not generate real names, emails, phone numbers, addresses, or private customer data.

## Generate Synthetic Data

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate the default sample CSVs:

```bash
python data_generator/generate_data.py --output-dir data/sample
```

The default generator creates:

- 50,000 sales
- 6,000 returns
- 500 products
- 20 stores
- 10,000 customers
- 150 employees

Run tests:

```bash
pytest
```

## Loading Data into Snowflake

1. Generate CSVs locally.

   ```bash
   python data_generator/generate_data.py --output-dir data/sample
   ```

2. Create the Snowflake database and raw tables.

   In Snowflake Snowsight, open and run the contents of:

   - `warehouse/01_create_database.sql`
   - `warehouse/02_create_raw_tables.sql`

   This creates the `RETAIL_RETURNS_ANALYTICS` database, the `RAW`, `STAGING`, `INTERMEDIATE`, `MARTS`, and `QA` schemas, the raw tables, a CSV file format, and an example internal stage.

3. Upload or stage the CSVs.

   Upload the files in `data/sample` to the `RAW.CSV_UPLOAD_STAGE` internal stage using Snowsight, or use your own stage and update the paths in `warehouse/03_load_data_template.sql`.

   Do not put credentials in this repo. If you use an external cloud stage, configure credentials securely in Snowflake.

4. Run `COPY INTO` commands.

   In Snowsight, open and run the contents of `warehouse/03_load_data_template.sql`.

   Replace paths such as `@RAW.CSV_UPLOAD_STAGE/sales.csv` if your files are uploaded under a folder or compressed as `.csv.gz`.

5. Confirm row counts.

   The load template ends with a row count query. For the default data, expected row counts are:

   - `RAW.SALES_RAW`: 50,000
   - `RAW.RETURNS_RAW`: 6,000
   - `RAW.PRODUCTS_RAW`: 500
   - `RAW.STORES_RAW`: 20
   - `RAW.CUSTOMERS_RAW`: 10,000
   - `RAW.EMPLOYEES_RAW`: 150
