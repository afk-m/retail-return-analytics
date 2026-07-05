# Databricks notebook source
# MAGIC %md
# MAGIC # 02 - Clean Silver Tables
# MAGIC
# MAGIC Read bronze Delta tables, standardize fields, apply basic data quality rules, and create cleaned silver Delta tables under `workspace.retail_returns`.

# COMMAND ----------

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

try:
    spark  # type: ignore[name-defined]
except NameError:
    spark = SparkSession.builder.appName("RetailReturnsSilverLayer").getOrCreate()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Silver tables are written to the same catalog and schema as the bronze tables.

# COMMAND ----------

CATALOG_NAME = "workspace"
SCHEMA_NAME = "retail_returns"
TABLE_PREFIX = f"{CATALOG_NAME}.{SCHEMA_NAME}"

RETURN_WINDOW_DAYS = 30
HIGH_VALUE_RETURN_THRESHOLD = 100.00


def bronze_table(name: str) -> str:
    return f"{TABLE_PREFIX}.bronze_{name}"


def silver_table(name: str) -> str:
    return f"{TABLE_PREFIX}.silver_{name}"


BRONZE_TABLES = {
    "sales": bronze_table("sales"),
    "returns": bronze_table("returns"),
    "products": bronze_table("products"),
    "stores": bronze_table("stores"),
    "customers": bronze_table("customers"),
    "employees": bronze_table("employees"),
}

SILVER_TABLES = {
    "sales": silver_table("sales"),
    "returns": silver_table("returns"),
    "products": silver_table("products"),
    "stores": silver_table("stores"),
    "customers": silver_table("customers"),
    "employees": silver_table("employees"),
}

PRIMARY_KEYS = {
    "sales": "sale_id",
    "returns": "return_id",
    "products": "product_id",
    "stores": "store_id",
    "customers": "customer_id",
    "employees": "employee_id",
}

# COMMAND ----------
# MAGIC %md
# MAGIC ## Helper Functions
# MAGIC
# MAGIC Reusable helpers keep type casting, boolean cleanup, table writes, and count checks consistent.

# COMMAND ----------

def clean_text(column_name: str):
    cleaned_value = F.lower(F.trim(F.col(column_name).cast("string")))
    return F.when(cleaned_value == "", F.lit(None).cast("string")).otherwise(cleaned_value)


def clean_date(column_name: str):
    return F.to_date(F.col(column_name).cast("string"))


def clean_double(column_name: str):
    return F.col(column_name).cast("double")


def clean_integer(column_name: str):
    return F.col(column_name).cast("int")


def clean_boolean(column_name: str):
    cleaned_value = F.lower(F.trim(F.col(column_name).cast("string")))
    return (
        F.when(cleaned_value.isin("true", "t", "yes", "y", "1"), F.lit(True))
        .when(cleaned_value.isin("false", "f", "no", "n", "0"), F.lit(False))
        .otherwise(F.lit(None).cast("boolean"))
    )


def write_silver_table(df: DataFrame, table_name: str) -> None:
    df.write.format("delta").mode("overwrite").saveAsTable(table_name)


def print_table_counts(title: str, tables: dict[str, str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    for table_name in tables.values():
        row_count = spark.table(table_name).count()
        print(f"{table_name}: {row_count:,} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Read Bronze Tables
# MAGIC
# MAGIC Load all bronze inputs before applying silver transformations.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TABLE_PREFIX}")

bronze_sales = spark.table(BRONZE_TABLES["sales"])
bronze_returns = spark.table(BRONZE_TABLES["returns"])
bronze_products = spark.table(BRONZE_TABLES["products"])
bronze_stores = spark.table(BRONZE_TABLES["stores"])
bronze_customers = spark.table(BRONZE_TABLES["customers"])
bronze_employees = spark.table(BRONZE_TABLES["employees"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Clean Sales
# MAGIC
# MAGIC The sales silver table stays at the sale-line grain. It casts dates, quantities, and amounts, removes missing sale IDs, removes negative sale amounts, and adds reusable sales metrics.

# COMMAND ----------

silver_sales = (
    bronze_sales
    .select(
        clean_text("sale_id").alias("sale_id"),
        clean_text("transaction_id").alias("transaction_id"),
        clean_date("sale_date").alias("sale_date"),
        clean_text("store_id").alias("store_id"),
        clean_text("customer_id").alias("customer_id"),
        clean_text("employee_id").alias("employee_id"),
        clean_text("product_id").alias("product_id"),
        clean_integer("quantity").alias("quantity"),
        clean_double("unit_price").alias("unit_price"),
        clean_double("discount_amount").alias("discount_amount"),
        clean_double("sale_amount").alias("sale_amount"),
        clean_text("payment_method").alias("payment_method"),
        clean_text("sales_channel").alias("sales_channel"),
    )
    .filter(F.col("sale_id").isNotNull())
    .filter(F.col("sale_amount").isNull() | (F.col("sale_amount") >= 0))
    .withColumn("gross_sale_amount", F.round(F.col("quantity") * F.col("unit_price"), 2))
    .withColumn(
        "net_sale_amount",
        F.when(
            F.col("gross_sale_amount").isNotNull(),
            F.round(
                F.col("gross_sale_amount") - F.coalesce(F.col("discount_amount"), F.lit(0.0)),
                2,
            ),
        ).otherwise(F.lit(None).cast("double")),
    )
    .withColumn(
        "discount_rate",
        F.when(
            F.col("gross_sale_amount") > 0,
            F.round(
                F.coalesce(F.col("discount_amount"), F.lit(0.0)) / F.col("gross_sale_amount"),
                4,
            ),
        ).otherwise(F.lit(None).cast("double")),
    )
)

write_silver_table(silver_sales, SILVER_TABLES["sales"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Clean Product, Store, Customer, and Employee Dimensions
# MAGIC
# MAGIC Dimension tables are cleaned at one row per business ID with normalized text, typed dates or amounts, and boolean cleanup where needed.

# COMMAND ----------

silver_products = (
    bronze_products
    .select(
        clean_text("product_id").alias("product_id"),
        clean_text("product_name").alias("product_name"),
        clean_text("product_category").alias("product_category"),
        clean_text("product_subcategory").alias("product_subcategory"),
        clean_text("brand").alias("brand"),
        clean_double("unit_price").alias("unit_price"),
        clean_double("cost").alias("cost"),
        clean_boolean("active_flag").alias("active_flag"),
    )
    .filter(F.col("product_id").isNotNull())
)

silver_stores = (
    bronze_stores
    .select(
        clean_text("store_id").alias("store_id"),
        clean_text("store_name").alias("store_name"),
        clean_text("city").alias("city"),
        clean_text("province").alias("province"),
        clean_text("region").alias("region"),
        clean_text("store_type").alias("store_type"),
        clean_date("open_date").alias("open_date"),
    )
    .filter(F.col("store_id").isNotNull())
)

silver_customers = (
    bronze_customers
    .select(
        clean_text("customer_id").alias("customer_id"),
        clean_text("loyalty_tier").alias("loyalty_tier"),
        clean_date("signup_date").alias("signup_date"),
        clean_text("city").alias("city"),
        clean_text("province").alias("province"),
    )
    .filter(F.col("customer_id").isNotNull())
)

silver_employees = (
    bronze_employees
    .select(
        clean_text("employee_id").alias("employee_id"),
        clean_text("store_id").alias("store_id"),
        clean_text("role").alias("role"),
        clean_date("hire_date").alias("hire_date"),
        clean_boolean("active_flag").alias("active_flag"),
    )
    .filter(F.col("employee_id").isNotNull())
)

write_silver_table(silver_products, SILVER_TABLES["products"])
write_silver_table(silver_stores, SILVER_TABLES["stores"])
write_silver_table(silver_customers, SILVER_TABLES["customers"])
write_silver_table(silver_employees, SILVER_TABLES["employees"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Clean Returns
# MAGIC
# MAGIC The returns silver table stays at the return-line grain. It joins to sales for `sale_date`, then adds timing, receipt, condition, high-value, and policy exception fields.

# COMMAND ----------

returns_base = (
    bronze_returns
    .select(
        clean_text("return_id").alias("return_id"),
        clean_text("sale_id").alias("sale_id"),
        clean_text("transaction_id").alias("transaction_id"),
        clean_date("return_date").alias("return_date"),
        clean_text("store_id").alias("store_id"),
        clean_text("customer_id").alias("customer_id"),
        clean_text("employee_id").alias("employee_id"),
        clean_text("product_id").alias("product_id"),
        clean_integer("return_quantity").alias("return_quantity"),
        clean_double("return_amount").alias("return_amount"),
        clean_text("return_reason").alias("return_reason"),
        clean_text("return_channel").alias("return_channel"),
        clean_text("refund_method").alias("refund_method"),
        clean_boolean("receipt_present").alias("receipt_present"),
        clean_text("item_condition").alias("item_condition"),
        clean_boolean("policy_exception_flag").alias("cleaned_policy_exception_flag"),
    )
    .filter(F.col("return_id").isNotNull())
    .filter(F.col("return_amount").isNull() | (F.col("return_amount") >= 0))
)

sales_dates = silver_sales.select("sale_id", "sale_date")

silver_returns = (
    returns_base
    .join(sales_dates, on="sale_id", how="left")
    .withColumn(
        "days_until_return",
        F.when(
            F.col("sale_date").isNotNull() & F.col("return_date").isNotNull(),
            F.datediff(F.col("return_date"), F.col("sale_date")),
        ).otherwise(F.lit(None).cast("int")),
    )
    .withColumn(
        "late_return_flag",
        F.when(
            F.col("days_until_return").isNotNull(),
            F.col("days_until_return") > RETURN_WINDOW_DAYS,
        ).otherwise(F.lit(None).cast("boolean")),
    )
    .withColumn(
        "no_receipt_flag",
        F.when(F.col("receipt_present").isNotNull(), ~F.col("receipt_present"))
        .otherwise(F.lit(None).cast("boolean")),
    )
    .withColumn(
        "damaged_or_defective_flag",
        F.coalesce(
            F.col("item_condition").isin("damaged", "defective")
            | F.col("return_reason").rlike("damaged|defective"),
            F.lit(False),
        ),
    )
    .withColumn(
        "high_value_return_flag",
        F.when(
            F.col("return_amount").isNotNull(),
            F.col("return_amount") >= HIGH_VALUE_RETURN_THRESHOLD,
        ).otherwise(F.lit(None).cast("boolean")),
    )
)

write_silver_table(silver_returns, SILVER_TABLES["returns"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Row Count Checks
# MAGIC
# MAGIC Print bronze and silver row counts after all silver tables are written.

# COMMAND ----------

print_table_counts("Bronze row counts", BRONZE_TABLES)
print_table_counts("Silver row counts", SILVER_TABLES)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Validation Checks
# MAGIC
# MAGIC Validate missing primary IDs, negative amounts, and returns that appear before their sales date.

# COMMAND ----------

print("\nValidation checks")
print("-----------------")
print("\nMissing primary IDs after cleaning")

for table_key, primary_key in PRIMARY_KEYS.items():
    table_name = SILVER_TABLES[table_key]
    missing_count = spark.table(table_name).filter(F.col(primary_key).isNull()).count()
    print(f"{table_name}.{primary_key}: {missing_count:,} missing")

negative_sales_count = (
    spark.table(SILVER_TABLES["sales"])
    .filter(F.col("sale_amount") < 0)
    .count()
)

negative_returns_count = (
    spark.table(SILVER_TABLES["returns"])
    .filter(F.col("return_amount") < 0)
    .count()
)

returns_before_sales_count = (
    spark.table(SILVER_TABLES["returns"])
    .filter(
        F.col("sale_date").isNotNull()
        & F.col("return_date").isNotNull()
        & (F.col("return_date") < F.col("sale_date"))
    )
    .count()
)

print("\nNegative amount checks after cleaning")
print(f"{SILVER_TABLES['sales']}.sale_amount < 0: {negative_sales_count:,} rows")
print(f"{SILVER_TABLES['returns']}.return_amount < 0: {negative_returns_count:,} rows")

print("\nReturn timing checks")
print(f"Returns before sales when sale_date is available: {returns_before_sales_count:,} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Silver Tables Created
# MAGIC
# MAGIC - `workspace.retail_returns.silver_sales`
# MAGIC - `workspace.retail_returns.silver_returns`
# MAGIC - `workspace.retail_returns.silver_products`
# MAGIC - `workspace.retail_returns.silver_stores`
# MAGIC - `workspace.retail_returns.silver_customers`
# MAGIC - `workspace.retail_returns.silver_employees`
