# Databricks notebook source
# MAGIC %md
# MAGIC # 03 - Build Gold Marts
# MAGIC
# MAGIC Build business-ready gold tables from cleaned silver Delta tables.
# MAGIC
# MAGIC These marts summarize sales, returns, product performance, store performance, return reasons, policy exceptions, and employee return activity.

# COMMAND ----------

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

try:
    spark  # type: ignore[name-defined]
except NameError:
    spark = SparkSession.builder.appName("RetailReturnsGoldLayer").getOrCreate()

# COMMAND ----------
# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Gold tables are written to `workspace.retail_returns`.

# COMMAND ----------

CATALOG_NAME = "workspace"
SCHEMA_NAME = "retail_returns"
TABLE_PREFIX = f"{CATALOG_NAME}.{SCHEMA_NAME}"


def silver_table(name: str) -> str:
    return f"{TABLE_PREFIX}.silver_{name}"


def gold_table(name: str) -> str:
    return f"{TABLE_PREFIX}.gold_{name}"


SILVER_TABLES = {
    "sales": silver_table("sales"),
    "returns": silver_table("returns"),
    "products": silver_table("products"),
    "stores": silver_table("stores"),
    "customers": silver_table("customers"),
    "employees": silver_table("employees"),
}

GOLD_TABLES = {
    "daily_sales_returns_summary": gold_table("daily_sales_returns_summary"),
    "return_rate_by_product": gold_table("return_rate_by_product"),
    "return_rate_by_store": gold_table("return_rate_by_store"),
    "return_reason_summary": gold_table("return_reason_summary"),
    "policy_exceptions": gold_table("policy_exceptions"),
    "employee_return_activity": gold_table("employee_return_activity"),
}

# COMMAND ----------
# MAGIC %md
# MAGIC ## Helper Functions
# MAGIC
# MAGIC These helpers keep gold writes, boolean counts, and row count checks readable.

# COMMAND ----------

def count_true(column_name: str, alias_name: str):
    return F.sum(
        F.when(F.col(column_name) == F.lit(True), F.lit(1)).otherwise(F.lit(0))
    ).alias(alias_name)


def safe_rate(numerator, denominator):
    return F.when(denominator > 0, F.round(numerator / denominator, 4)).otherwise(
        F.lit(None).cast("double")
    )


def write_gold_table(df: DataFrame, table_name: str) -> None:
    df.write.format("delta").mode("overwrite").saveAsTable(table_name)


def print_table_counts(title: str, tables: dict[str, str]) -> None:
    print(f"\n{title}")
    print("-" * len(title))

    for table_name in tables.values():
        row_count = spark.table(table_name).count()
        print(f"{table_name}: {row_count:,} rows")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Read Silver Tables
# MAGIC
# MAGIC Load cleaned silver facts and dimensions as the source for all gold marts.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {TABLE_PREFIX}")

silver_sales = spark.table(SILVER_TABLES["sales"])
silver_returns = spark.table(SILVER_TABLES["returns"])
silver_products = spark.table(SILVER_TABLES["products"])
silver_stores = spark.table(SILVER_TABLES["stores"])
silver_customers = spark.table(SILVER_TABLES["customers"])
silver_employees = spark.table(SILVER_TABLES["employees"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Daily Sales Returns Summary
# MAGIC
# MAGIC Summarize sales and returns by business date for trend analysis.

# COMMAND ----------

sales_daily = (
    silver_sales
    .withColumnRenamed("sale_date", "activity_date")
    .groupBy("activity_date")
    .agg(
        F.countDistinct("sale_id").alias("sale_count"),
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("gross_sale_amount"), 2).alias("gross_sales_amount"),
        F.round(F.sum("net_sale_amount"), 2).alias("net_sales_amount"),
        F.round(F.sum("sale_amount"), 2).alias("recorded_sales_amount"),
    )
)

returns_daily = (
    silver_returns
    .withColumnRenamed("return_date", "activity_date")
    .groupBy("activity_date")
    .agg(
        F.countDistinct("return_id").alias("return_count"),
        F.sum("return_quantity").alias("units_returned"),
        F.round(F.sum("return_amount"), 2).alias("return_amount"),
        count_true("late_return_flag", "late_return_count"),
        count_true("no_receipt_flag", "no_receipt_return_count"),
        count_true("high_value_return_flag", "high_value_return_count"),
    )
)

gold_daily_sales_returns_summary = (
    sales_daily
    .join(returns_daily, on="activity_date", how="full")
    .fillna(
        0,
        subset=[
            "sale_count",
            "units_sold",
            "gross_sales_amount",
            "net_sales_amount",
            "recorded_sales_amount",
            "return_count",
            "units_returned",
            "return_amount",
            "late_return_count",
            "no_receipt_return_count",
            "high_value_return_count",
        ],
    )
    .withColumn(
        "return_rate_by_units",
        safe_rate(F.col("units_returned"), F.col("units_sold")),
    )
    .withColumn(
        "return_rate_by_amount",
        safe_rate(F.col("return_amount"), F.col("net_sales_amount")),
    )
    .orderBy("activity_date")
)

write_gold_table(
    gold_daily_sales_returns_summary,
    GOLD_TABLES["daily_sales_returns_summary"],
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Return Rate By Product
# MAGIC
# MAGIC Combine product attributes with sales and return metrics to compare product-level return behavior.

# COMMAND ----------

sales_by_product = (
    silver_sales
    .groupBy("product_id")
    .agg(
        F.countDistinct("sale_id").alias("sale_count"),
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("gross_sale_amount"), 2).alias("gross_sales_amount"),
        F.round(F.sum("net_sale_amount"), 2).alias("net_sales_amount"),
    )
)

returns_by_product = (
    silver_returns
    .groupBy("product_id")
    .agg(
        F.countDistinct("return_id").alias("return_count"),
        F.sum("return_quantity").alias("units_returned"),
        F.round(F.sum("return_amount"), 2).alias("return_amount"),
        count_true("damaged_or_defective_flag", "damaged_or_defective_return_count"),
        count_true("high_value_return_flag", "high_value_return_count"),
    )
)

gold_return_rate_by_product = (
    silver_products
    .join(sales_by_product, on="product_id", how="full")
    .join(returns_by_product, on="product_id", how="full")
    .fillna(
        0,
        subset=[
            "sale_count",
            "units_sold",
            "gross_sales_amount",
            "net_sales_amount",
            "return_count",
            "units_returned",
            "return_amount",
            "damaged_or_defective_return_count",
            "high_value_return_count",
        ],
    )
    .withColumn(
        "return_rate_by_units",
        safe_rate(F.col("units_returned"), F.col("units_sold")),
    )
    .withColumn(
        "return_rate_by_amount",
        safe_rate(F.col("return_amount"), F.col("net_sales_amount")),
    )
)

write_gold_table(gold_return_rate_by_product, GOLD_TABLES["return_rate_by_product"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Return Rate By Store
# MAGIC
# MAGIC Summarize store-level sales and return activity for operational comparison.

# COMMAND ----------

sales_by_store = (
    silver_sales
    .groupBy("store_id")
    .agg(
        F.countDistinct("sale_id").alias("sale_count"),
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("net_sale_amount"), 2).alias("net_sales_amount"),
    )
)

returns_by_store = (
    silver_returns
    .groupBy("store_id")
    .agg(
        F.countDistinct("return_id").alias("return_count"),
        F.sum("return_quantity").alias("units_returned"),
        F.round(F.sum("return_amount"), 2).alias("return_amount"),
        count_true("late_return_flag", "late_return_count"),
        count_true("no_receipt_flag", "no_receipt_return_count"),
        count_true("cleaned_policy_exception_flag", "policy_exception_count"),
    )
)

gold_return_rate_by_store = (
    silver_stores
    .join(sales_by_store, on="store_id", how="full")
    .join(returns_by_store, on="store_id", how="full")
    .fillna(
        0,
        subset=[
            "sale_count",
            "units_sold",
            "net_sales_amount",
            "return_count",
            "units_returned",
            "return_amount",
            "late_return_count",
            "no_receipt_return_count",
            "policy_exception_count",
        ],
    )
    .withColumn(
        "return_rate_by_units",
        safe_rate(F.col("units_returned"), F.col("units_sold")),
    )
    .withColumn(
        "return_rate_by_amount",
        safe_rate(F.col("return_amount"), F.col("net_sales_amount")),
    )
)

write_gold_table(gold_return_rate_by_store, GOLD_TABLES["return_rate_by_store"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Return Reason Summary
# MAGIC
# MAGIC Use Spark SQL to summarize return reasons and the most important return quality flags.

# COMMAND ----------

silver_returns.createOrReplaceTempView("silver_returns_for_reason_summary")

gold_return_reason_summary = spark.sql(
    """
    SELECT
        COALESCE(return_reason, 'unknown') AS return_reason,
        COUNT(DISTINCT return_id) AS return_count,
        SUM(return_quantity) AS units_returned,
        ROUND(SUM(return_amount), 2) AS return_amount,
        ROUND(AVG(days_until_return), 2) AS avg_days_until_return,
        SUM(CASE WHEN late_return_flag THEN 1 ELSE 0 END) AS late_return_count,
        SUM(CASE WHEN no_receipt_flag THEN 1 ELSE 0 END) AS no_receipt_return_count,
        SUM(CASE WHEN damaged_or_defective_flag THEN 1 ELSE 0 END) AS damaged_or_defective_return_count,
        SUM(CASE WHEN cleaned_policy_exception_flag THEN 1 ELSE 0 END) AS policy_exception_count,
        SUM(CASE WHEN high_value_return_flag THEN 1 ELSE 0 END) AS high_value_return_count
    FROM silver_returns_for_reason_summary
    GROUP BY COALESCE(return_reason, 'unknown')
    """
)

write_gold_table(gold_return_reason_summary, GOLD_TABLES["return_reason_summary"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Policy Exceptions
# MAGIC
# MAGIC Create a return-level exception table enriched with product, store, and employee context.

# COMMAND ----------

gold_policy_exceptions = (
    silver_returns
    .filter(F.col("cleaned_policy_exception_flag") == F.lit(True))
    .join(
        silver_products.select(
            "product_id",
            "product_name",
            "product_category",
            "product_subcategory",
            "brand",
        ),
        on="product_id",
        how="left",
    )
    .join(
        silver_stores.select(
            "store_id",
            "store_name",
            "city",
            "province",
            "region",
            "store_type",
        ),
        on="store_id",
        how="left",
    )
    .join(
        silver_employees.select(
            "employee_id",
            F.col("role").alias("employee_role"),
            F.col("active_flag").alias("employee_active_flag"),
        ),
        on="employee_id",
        how="left",
    )
    .select(
        "return_id",
        "sale_id",
        "transaction_id",
        "return_date",
        "sale_date",
        "days_until_return",
        "store_id",
        "store_name",
        "city",
        "province",
        "region",
        "product_id",
        "product_name",
        "product_category",
        "product_subcategory",
        "brand",
        "employee_id",
        "employee_role",
        "employee_active_flag",
        "customer_id",
        "return_quantity",
        "return_amount",
        "return_reason",
        "return_channel",
        "refund_method",
        "receipt_present",
        "item_condition",
        "late_return_flag",
        "no_receipt_flag",
        "damaged_or_defective_flag",
        "high_value_return_flag",
        "cleaned_policy_exception_flag",
    )
)

write_gold_table(gold_policy_exceptions, GOLD_TABLES["policy_exceptions"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Employee Return Activity
# MAGIC
# MAGIC Summarize sales and returns by employee to highlight return activity patterns.

# COMMAND ----------

sales_by_employee = (
    silver_sales
    .groupBy("employee_id")
    .agg(
        F.countDistinct("sale_id").alias("sale_count"),
        F.sum("quantity").alias("units_sold"),
        F.round(F.sum("net_sale_amount"), 2).alias("net_sales_amount"),
    )
)

returns_by_employee = (
    silver_returns
    .groupBy("employee_id")
    .agg(
        F.countDistinct("return_id").alias("return_count"),
        F.sum("return_quantity").alias("units_returned"),
        F.round(F.sum("return_amount"), 2).alias("return_amount"),
        count_true("late_return_flag", "late_return_count"),
        count_true("no_receipt_flag", "no_receipt_return_count"),
        count_true("cleaned_policy_exception_flag", "policy_exception_count"),
        count_true("high_value_return_flag", "high_value_return_count"),
    )
)

gold_employee_return_activity = (
    silver_employees
    .join(sales_by_employee, on="employee_id", how="full")
    .join(returns_by_employee, on="employee_id", how="full")
    .fillna(
        0,
        subset=[
            "sale_count",
            "units_sold",
            "net_sales_amount",
            "return_count",
            "units_returned",
            "return_amount",
            "late_return_count",
            "no_receipt_return_count",
            "policy_exception_count",
            "high_value_return_count",
        ],
    )
    .withColumn(
        "return_rate_by_units",
        safe_rate(F.col("units_returned"), F.col("units_sold")),
    )
    .withColumn(
        "return_rate_by_amount",
        safe_rate(F.col("return_amount"), F.col("net_sales_amount")),
    )
)

write_gold_table(gold_employee_return_activity, GOLD_TABLES["employee_return_activity"])

# COMMAND ----------
# MAGIC %md
# MAGIC ## Row Count Checks
# MAGIC
# MAGIC Print row counts for all silver inputs and gold outputs.

# COMMAND ----------

print_table_counts("Silver row counts", SILVER_TABLES)
print_table_counts("Gold row counts", GOLD_TABLES)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold Tables Created
# MAGIC
# MAGIC - `workspace.retail_returns.gold_daily_sales_returns_summary`
# MAGIC - `workspace.retail_returns.gold_return_rate_by_product`
# MAGIC - `workspace.retail_returns.gold_return_rate_by_store`
# MAGIC - `workspace.retail_returns.gold_return_reason_summary`
# MAGIC - `workspace.retail_returns.gold_policy_exceptions`
# MAGIC - `workspace.retail_returns.gold_employee_return_activity`
