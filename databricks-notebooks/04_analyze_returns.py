# Databricks notebook source
# MAGIC %md
# MAGIC # 04 - Analyze Returns
# MAGIC
# MAGIC Read gold marts and show simple return analytics outputs with `display()`.

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

try:
    spark  # type: ignore[name-defined]
except NameError:
    spark = SparkSession.builder.appName("RetailReturnsAnalysis").getOrCreate()

try:
    display  # type: ignore[name-defined]
except NameError:
    def display(df):  # type: ignore[no-redef]
        df.show(50, truncate=False)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Configuration
# MAGIC
# MAGIC Gold tables are read from `workspace.retail_returns`.

# COMMAND ----------

CATALOG_NAME = "workspace"
SCHEMA_NAME = "retail_returns"
TABLE_PREFIX = f"{CATALOG_NAME}.{SCHEMA_NAME}"


def gold_table(name: str) -> str:
    return f"{TABLE_PREFIX}.gold_{name}"


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
# MAGIC ## Overview
# MAGIC
# MAGIC Summarize total sales, returns, return rates, and exception counts across the gold daily mart.

# COMMAND ----------

daily_summary = spark.table(GOLD_TABLES["daily_sales_returns_summary"])
product_returns = spark.table(GOLD_TABLES["return_rate_by_product"])
store_returns = spark.table(GOLD_TABLES["return_rate_by_store"])
reason_summary = spark.table(GOLD_TABLES["return_reason_summary"])
policy_exceptions = spark.table(GOLD_TABLES["policy_exceptions"])
employee_activity = spark.table(GOLD_TABLES["employee_return_activity"])

overview = (
    daily_summary
    .agg(
        F.countDistinct("activity_date").alias("active_dates"),
        F.sum("sale_count").alias("total_sales"),
        F.sum("return_count").alias("total_returns"),
        F.round(F.sum("net_sales_amount"), 2).alias("total_net_sales_amount"),
        F.round(F.sum("return_amount"), 2).alias("total_return_amount"),
        F.sum("late_return_count").alias("late_returns"),
        F.sum("no_receipt_return_count").alias("no_receipt_returns"),
        F.sum("high_value_return_count").alias("high_value_returns"),
    )
    .withColumn(
        "overall_return_rate_by_amount",
        F.when(
            F.col("total_net_sales_amount") > 0,
            F.round(F.col("total_return_amount") / F.col("total_net_sales_amount"), 4),
        ).otherwise(F.lit(None).cast("double")),
    )
)

display(overview)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Daily Trends
# MAGIC
# MAGIC Review daily sales, returns, and return rates over time.

# COMMAND ----------

display(
    daily_summary
    .orderBy("activity_date")
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Product Returns
# MAGIC
# MAGIC Identify products with the largest return amounts and highest return rates.

# COMMAND ----------

display(
    product_returns
    .filter(F.col("return_count") > 0)
    .orderBy(F.desc("return_amount"), F.desc("return_rate_by_amount"))
    .limit(25)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Store Returns
# MAGIC
# MAGIC Compare store-level return volume, return amount, and policy exception activity.

# COMMAND ----------

display(
    store_returns
    .orderBy(F.desc("return_amount"), F.desc("return_rate_by_amount"))
    .limit(25)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Return Reasons
# MAGIC
# MAGIC Summarize why items are returned and how often each reason is tied to late, no-receipt, damaged, or exception cases.

# COMMAND ----------

display(
    reason_summary
    .orderBy(F.desc("return_count"), F.desc("return_amount"))
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Policy Exceptions
# MAGIC
# MAGIC Review high-risk return records where the cleaned policy exception flag is true.

# COMMAND ----------

display(
    policy_exceptions
    .orderBy(F.desc("return_amount"), F.desc("return_date"))
    .limit(50)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Employee Activity
# MAGIC
# MAGIC Compare employee-level return activity, return rates, and exception counts.

# COMMAND ----------

display(
    employee_activity
    .orderBy(F.desc("return_count"), F.desc("policy_exception_count"))
    .limit(50)
)
