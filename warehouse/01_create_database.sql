-- Retail Returns Analytics Warehouse
-- 01, to be run first in Snowflake worksheet

CREATE DATABASE IF NOT EXISTS RETAIL_RETURNS_ANALYTICS
  COMMENT = 'Portfolio warehouse for synthetic retail sales and returns analytics.';

USE DATABASE RETAIL_RETURNS_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS RAW
  COMMENT = 'Landing schema for generated CSV files loaded with minimal changes.';

CREATE SCHEMA IF NOT EXISTS STAGING
  COMMENT = 'Future dbt staging models.';

CREATE SCHEMA IF NOT EXISTS INTERMEDIATE
  COMMENT = 'Future dbt intermediate models.';

CREATE SCHEMA IF NOT EXISTS MARTS
  COMMENT = 'Future analytics marts.';

CREATE SCHEMA IF NOT EXISTS QA
  COMMENT = 'Future data quality checks and audit outputs.';

