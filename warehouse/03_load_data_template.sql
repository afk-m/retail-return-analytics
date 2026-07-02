-- Retail Returns Analytics Warehouse
-- 03, run this after creating the raw tables and uploading CSVs to RAW.CSV_UPLOAD_STAGE.
--
-- replace stage paths if uploaded files are under a folder or were compressed.
-- Examples:
--   @RAW.CSV_UPLOAD_STAGE/sales.csv
--   @RAW.CSV_UPLOAD_STAGE/sample/sales.csv
--   @RAW.CSV_UPLOAD_STAGE/sales.csv.gz
--
-- Snowsight upload path:
--   Data > Databases > RETAIL_RETURNS_ANALYTICS > RAW > Stages > CSV_UPLOAD_STAGE
--
-- SnowSQL PUT example only, not a worksheet command, just for reference:
--   PUT file:///absolute/path/to/retail-return-analytics/data/sample/sales.csv @RAW.CSV_UPLOAD_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;

USE DATABASE RETAIL_RETURNS_ANALYTICS;
USE SCHEMA RAW;

-- confirm the staged files before loading.
LIST @RAW.CSV_UPLOAD_STAGE;

COPY INTO RAW.PRODUCTS_RAW (
  product_id,
  product_name,
  product_category,
  product_subcategory,
  brand,
  unit_price,
  cost,
  active_flag,
  loaded_at,
  source_file
)
FROM (
  SELECT
    $1::STRING,
    $2::STRING,
    $3::STRING,
    $4::STRING,
    $5::STRING,
    $6::NUMBER(10, 2),
    $7::NUMBER(10, 2),
    $8::BOOLEAN,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    METADATA$FILENAME::STRING
  FROM @RAW.CSV_UPLOAD_STAGE/products.csv
)
FILE_FORMAT = (FORMAT_NAME = RAW.CSV_FILE_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW.STORES_RAW (
  store_id,
  store_name,
  city,
  province,
  region,
  store_type,
  open_date,
  loaded_at,
  source_file
)
FROM (
  SELECT
    $1::STRING,
    $2::STRING,
    $3::STRING,
    $4::STRING,
    $5::STRING,
    $6::STRING,
    $7::DATE,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    METADATA$FILENAME::STRING
  FROM @RAW.CSV_UPLOAD_STAGE/stores.csv
)
FILE_FORMAT = (FORMAT_NAME = RAW.CSV_FILE_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW.CUSTOMERS_RAW (
  customer_id,
  loyalty_tier,
  signup_date,
  city,
  province,
  loaded_at,
  source_file
)
FROM (
  SELECT
    $1::STRING,
    $2::STRING,
    $3::DATE,
    $4::STRING,
    $5::STRING,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    METADATA$FILENAME::STRING
  FROM @RAW.CSV_UPLOAD_STAGE/customers.csv
)
FILE_FORMAT = (FORMAT_NAME = RAW.CSV_FILE_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW.EMPLOYEES_RAW (
  employee_id,
  store_id,
  role,
  hire_date,
  active_flag,
  loaded_at,
  source_file
)
FROM (
  SELECT
    $1::STRING,
    $2::STRING,
    $3::STRING,
    $4::DATE,
    $5::BOOLEAN,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    METADATA$FILENAME::STRING
  FROM @RAW.CSV_UPLOAD_STAGE/employees.csv
)
FILE_FORMAT = (FORMAT_NAME = RAW.CSV_FILE_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW.SALES_RAW (
  sale_id,
  transaction_id,
  sale_date,
  store_id,
  customer_id,
  employee_id,
  product_id,
  quantity,
  unit_price,
  discount_amount,
  sale_amount,
  payment_method,
  sales_channel,
  loaded_at,
  source_file
)
FROM (
  SELECT
    $1::STRING,
    $2::STRING,
    $3::DATE,
    $4::STRING,
    $5::STRING,
    $6::STRING,
    $7::STRING,
    $8::NUMBER(10, 0),
    $9::NUMBER(10, 2),
    $10::NUMBER(10, 2),
    $11::NUMBER(10, 2),
    $12::STRING,
    $13::STRING,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    METADATA$FILENAME::STRING
  FROM @RAW.CSV_UPLOAD_STAGE/sales.csv
)
FILE_FORMAT = (FORMAT_NAME = RAW.CSV_FILE_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

COPY INTO RAW.RETURNS_RAW (
  return_id,
  sale_id,
  transaction_id,
  return_date,
  store_id,
  customer_id,
  employee_id,
  product_id,
  return_quantity,
  return_amount,
  return_reason,
  return_channel,
  refund_method,
  receipt_present,
  item_condition,
  policy_exception_flag,
  loaded_at,
  source_file
)
FROM (
  SELECT
    $1::STRING,
    $2::STRING,
    $3::STRING,
    $4::DATE,
    $5::STRING,
    $6::STRING,
    $7::STRING,
    $8::STRING,
    $9::NUMBER(10, 0),
    $10::NUMBER(10, 2),
    $11::STRING,
    $12::STRING,
    $13::STRING,
    $14::BOOLEAN,
    $15::STRING,
    $16::BOOLEAN,
    CURRENT_TIMESTAMP()::TIMESTAMP_NTZ,
    METADATA$FILENAME::STRING
  FROM @RAW.CSV_UPLOAD_STAGE/returns.csv
)
FILE_FORMAT = (FORMAT_NAME = RAW.CSV_FILE_FORMAT)
ON_ERROR = 'ABORT_STATEMENT';

-- confirm loaded row counts
SELECT 'PRODUCTS_RAW' AS table_name, COUNT(*) AS row_count FROM RAW.PRODUCTS_RAW
UNION ALL
SELECT 'STORES_RAW', COUNT(*) FROM RAW.STORES_RAW
UNION ALL
SELECT 'CUSTOMERS_RAW', COUNT(*) FROM RAW.CUSTOMERS_RAW
UNION ALL
SELECT 'EMPLOYEES_RAW', COUNT(*) FROM RAW.EMPLOYEES_RAW
UNION ALL
SELECT 'SALES_RAW', COUNT(*) FROM RAW.SALES_RAW
UNION ALL
SELECT 'RETURNS_RAW', COUNT(*) FROM RAW.RETURNS_RAW
ORDER BY table_name;
