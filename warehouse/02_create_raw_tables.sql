-- Retail Returns Analytics Warehouse
-- 02, run this after 01_create_database.sql
-- these tables intentionally mirror the generated CSVs with only simple load metadata added

USE DATABASE RETAIL_RETURNS_ANALYTICS;
USE SCHEMA RAW;

CREATE OR REPLACE FILE FORMAT RAW.CSV_FILE_FORMAT
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TRIM_SPACE = TRUE
  EMPTY_FIELD_AS_NULL = TRUE
  NULL_IF = ('', 'NULL', 'null')
  ERROR_ON_COLUMN_COUNT_MISMATCH = TRUE
  DATE_FORMAT = 'AUTO'
  TIMESTAMP_FORMAT = 'AUTO'
  COMPRESSION = AUTO
  COMMENT = 'CSV format for synthetic retail returns analytics files.';

-- internal stage example. upload generated CSVs from data/sample here using Snowsight, SnowSQL PUT, or replace this stage with another internal/external stage if need be in the future
CREATE OR REPLACE STAGE RAW.CSV_UPLOAD_STAGE
  FILE_FORMAT = RAW.CSV_FILE_FORMAT
  COMMENT = 'Stage for generated CSV files such as sales.csv and returns.csv.';

CREATE OR REPLACE TABLE RAW.PRODUCTS_RAW (
  product_id STRING,
  product_name STRING,
  product_category STRING,
  product_subcategory STRING,
  brand STRING,
  unit_price NUMBER(10, 2),
  cost NUMBER(10, 2),
  active_flag BOOLEAN,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);

CREATE OR REPLACE TABLE RAW.STORES_RAW (
  store_id STRING,
  store_name STRING,
  city STRING,
  province STRING,
  region STRING,
  store_type STRING,
  open_date DATE,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);

CREATE OR REPLACE TABLE RAW.CUSTOMERS_RAW (
  customer_id STRING,
  loyalty_tier STRING,
  signup_date DATE,
  city STRING,
  province STRING,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);

CREATE OR REPLACE TABLE RAW.EMPLOYEES_RAW (
  employee_id STRING,
  store_id STRING,
  role STRING,
  hire_date DATE,
  active_flag BOOLEAN,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);

CREATE OR REPLACE TABLE RAW.SALES_RAW (
  sale_id STRING,
  transaction_id STRING,
  sale_date DATE,
  store_id STRING,
  customer_id STRING,
  employee_id STRING,
  product_id STRING,
  quantity NUMBER(10, 0),
  unit_price NUMBER(10, 2),
  discount_amount NUMBER(10, 2),
  sale_amount NUMBER(10, 2),
  payment_method STRING,
  sales_channel STRING,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);

CREATE OR REPLACE TABLE RAW.RETURNS_RAW (
  return_id STRING,
  sale_id STRING,
  transaction_id STRING,
  return_date DATE,
  store_id STRING,
  customer_id STRING,
  employee_id STRING,
  product_id STRING,
  return_quantity NUMBER(10, 0),
  return_amount NUMBER(10, 2),
  return_reason STRING,
  return_channel STRING,
  refund_method STRING,
  receipt_present BOOLEAN,
  item_condition STRING,
  policy_exception_flag BOOLEAN,
  loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  source_file STRING
);

