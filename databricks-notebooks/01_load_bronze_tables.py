# Databricks notebook source
# MAGIC %md
# MAGIC # 01 - Load Bronze Tables
# MAGIC
# MAGIC Copy Databricks UI-loaded source tables from `workspace.default` into bronze Delta tables under `workspace.retail_returns`.
# MAGIC
# MAGIC The bronze layer preserves the source structure and gives later notebooks a stable lakehouse input.

# COMMAND ----------

from pyspark.sql import DataFrame, SparkSession

try:
    spark  # type: ignore[name-defined]
except NameError:
    spark = SparkSession.builder.appName("RetailReturnsBronzeLayer").getOrCreate()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC The source tables are expected to exist in `workspace.default`. The bronze tables are written to `workspace.retail_returns`.

# COMMAND ----------

SOURCE_CATALOG = "workspace"
SOURCE_SCHEMA = "default"

TARGET_CATALOG = "workspace"
TARGET_SCHEMA = "retail_returns"
TARGET_PREFIX = f"{TARGET_CATALOG}.{TARGET_SCHEMA}"

SOURCE_TABLES = {
    "sales": f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.sales",
    "returns": f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.returns",
    "products": f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.products",
    "stores": f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.stores",
    "customers": f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.customers",
    "employees": f"{SOURCE_CATALOG}.{SOURCE_SCHEMA}.employees",
}

BRONZE_TABLES = {
    name: f"{TARGET_PREFIX}.bronze_{name}"
    for name in SOURCE_TABLES
}

# COMMAND ----------
# MAGIC %md
# MAGIC ## Create Target Schema
# MAGIC
# MAGIC Create the `retail_returns` schema if it does not already exist.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TARGET_PREFIX}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Helper Functions
# MAGIC
# MAGIC These helpers keep table writes and row count checks consistent.

# COMMAND ----------

def write_bronze_table(df: DataFrame, table_name: str) -> None:
    df.write.format("delta").mode("overwrite").saveAsTable(table_name)


def print_table_counts(title: str, tables: dict[str, str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    for table_name in tables.values():
        row_count = spark.table(table_name).count()
        print(f"{table_name}: {row_count:,} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Load Bronze Tables
# MAGIC
# MAGIC Each source table is copied into a bronze Delta table with the same business subject name.

# COMMAND ----------

for table_key, source_table in SOURCE_TABLES.items():
    bronze_table = BRONZE_TABLES[table_key]
    source_df = spark.table(source_table)

    write_bronze_table(source_df, bronze_table)

    print(f"Created {bronze_table}: {source_df.count():,} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Row Count Checks
# MAGIC
# MAGIC Compare source and bronze row counts after the copy completes.

# COMMAND ----------

print_table_counts("Source row counts", SOURCE_TABLES)
print_table_counts("Bronze row counts", BRONZE_TABLES)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Bronze Tables Created
# MAGIC
# MAGIC - `workspace.retail_returns.bronze_sales`
# MAGIC - `workspace.retail_returns.bronze_returns`
# MAGIC - `workspace.retail_returns.bronze_products`
# MAGIC - `workspace.retail_returns.bronze_stores`
# MAGIC - `workspace.retail_returns.bronze_customers`
# MAGIC - `workspace.retail_returns.bronze_employees`
