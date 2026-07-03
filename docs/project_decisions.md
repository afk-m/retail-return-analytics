# Project Decisions

This document explains the main design choices behind the Retail Returns Analytics Warehouse. Some of this may seem obvious, but it's mainly to communicate the fact that I know standard practices when it comes to data warehousing.

## Synthetic Data Usage

The project is intended for a portfolio, so it avoids real customer, employee, and transaction data. Synthetic data makes the project safe to share publicly while still allowing realistic analytics workflows. And as you can guess, it's not really easy to get your hands on real data that retail stores use for analytics.

I created something similar for my capstone project, FRAUDS. However, in this case, distribution and features don't matter, since this project is mostly focused with loading/storing data and visualizing it. For example, the item names are definitely not realistic and the sales probably won't support the company, but as long as there is a connection between CSV tables and the pipeline works that's really all that matters. And we can be sure that this can be used with real data as well!

The generator here creates fake sales, returns, products, stores, customers, and employees. Customer and employee records intentionally exclude names, emails, phone numbers, and street addresses- they aren't too relevant for downstream analytics.

## Why Snowflake Was Used

Snowflake is commonly used for cloud data warehousing and is a good fit for demonstrating:

- SQL-based raw ingestion
- Separate schemas for raw, staging, intermediate, marts, and QA layers
- CSV loading through stages and `COPY INTO`
- A warehouse structure that can later support BI tools or applications

For this project, Snowflake is used at portfolio scale, not as a production deployment.

## Why dbt Was Used

dbt Core is used to transform and test the data after it lands in Snowflake. It provides:

- Version-controlled SQL transformations
- Clear model lineage
- Reusable staging, intermediate, and mart layers
- Built-in testing patterns for common data quality checks

dbt also makes the project easier for technical reviewers to inspect because the transformation logic is organized by each layer

## RAW, STAGING, INTERMEDIATE, and MARTS Layers

The layers separate responsibilities:

- RAW keeps the loaded CSV data close to the original files
- STAGING standardizes types, names, and categorical values (cleaning)
- INTERMEDIATE joins and enriches data while keeping reusable business logic separate
- MARTS provides final reporting tables for business questions and the dashboard

This structure keeps the project readable and avoids mixing ingestion, cleaning, joining, and reporting logic in one place, keeping it traceable as well.

## Why dbt Tests Were Added

dbt tests are very handy and can help confirm that important assumptions hold up. This project includes tests for:

- Unique primary identifiers
- Not-null key fields
- Accepted categorical values
- Relationships between records
- Non-empty key tables

The non-empty tests are important because some dbt tests, such as `not_null` and `unique`, can pass on a table with zero rows.

## Why Mart Tables Were Created (Instead of Querying Raw Tables Directly)

Raw tables are useful for preserving the original load, but they are not ideal for dashboard queries. Mart tables provide some pretty helpful things:

- Clean business metrics
- Stable grains
- Reusable definitions for return rate, exception flags, and net revenue
- Overall simpler dashboard SQL

This makes the dashboard easier to understand and keeps business logic in dbt instead of hiding it inside the Streamlit app.

## Why Streamlit Was Used

Streamlit is lightweight and fast for a portfolio dashboard. It lets the project show the final marts in an interactive way without adding a separate BI platform. Not only that but it's an easier Python implementation than Flask which I can appreciate.

The dashboard is simple by design:

- It connects to Snowflake with environment variables
- It queries only MART tables
- It uses Plotly for readable charts
- It avoids hardcoded credentials

## What Would Change in a Production Version

A production version would keep the same basic idea, but add more automation, security, monitoring, and separation between environments that would be expected frmo an enterprise deployment.

### Scheduled ingestion and orchestration

In this portfolio version, CSV files are generated and loaded manually. In production, new sales and returns files would likely arrive on a schedule or be triggered by upstream systems.

**Rationale:** Manual loading is fine for a portfolio project but production pipelines need to run without someone clicking buttons every day.

**Possible tools:** Snowflake Tasks, Snowflake Streams, Airflow, Dagster, Prefect, or GitHub Actions.

**How I would implement it:**  
I would land new files in a cloud storage location such as AWS S3, then use Snowflake stages and `COPY INTO` to load them into RAW tables. Snowflake Streams could track new or changed rows, and Snowflake Tasks could run loading or transformation SQL on a schedule or when new data arrives. Snowflake Tasks are designed to automate SQL and stored procedure work, and triggered tasks can run when stream data changes.

In the past I have used job scheduling software and Bash scripting to achieve this in a development environment.

---

### Incremental dbt models for larger tables

This project can rebuild all models because the data is small. In production, sales and returns tables could contain millions or billions of rows.

**Rationale:** Rebuilding every table from scratch wastes compute and slows down the pipeline.

**Possible tools:** dbt incremental models, Snowflake merge strategy, partition/date filters.

**How I would implement it:**  
I would convert large fact models, such as daily sales/returns and product return-rate tables, into dbt incremental models. The model would only process new or changed records based on fields like `sale_date`, `return_date`, `loaded_at`, or `updated_at`. dbt incremental models are meant to reduce transformation time by only transforming new or changed data instead of rebuilding the full table each run.

---

### More complete observability and alerting

This project has dbt tests, however production requires some stronger monitoring around failures, row counts, freshness, and metric changes that very well may happen.

**Rationale:** A pipeline can “run” but still produce bad or stale data. Teams need to know when something breaks before business users notice.

**Possible tools:** dbt tests, dbt source freshness, Elementary, Monte Carlo, Datadog, Snowflake query history, Slack/email alerts, GitHub Actions notifications.

**How I would implement it:**  
I would add source freshness checks, non-empty table checks, row-count trend checks, accepted-value checks, and anomaly checks for return rates. Failed dbt jobs could send alerts through Slack or email. I would also track pipeline runtime, failed models, and Snowflake query cost so issues are visible early.

---

### Role-based access control

This project uses a simple development setup. In production, not every user should have the same permissions.

**Rationale:** Analysts, engineers, dashboard users, and admins need different access levels. This protects data and reduces the chance of accidental changes.

**Possible tools:** Snowflake RBAC, custom Snowflake roles, grants, separate read/write roles, integrated with enterprise single sign-on.

**How I would implement it:**  
I would create roles like `retail_loader_role`, `retail_transformer_role`, `retail_analyst_role`, and `retail_dashboard_role`. The loader role could write to RAW, the transformer role could build STAGING/INTERMEDIATE/MARTS, and analysts could only read from MARTS. Snowflake’s access control model supports assigning privileges to roles, then assigning roles to users.

---

### Secrets management through a secure platform

This portfolio project uses local environment variables (located in ~/.dbt and exported in the terminal). In production, credentials should not live in local files or source code.

**Rationale:** Database passwords, tokens, and keys need to be stored and rotated securely.

**Possible tools:** GitHub Actions Secrets, Streamlit Secrets, AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, Snowflake key-pair authentication.

**How I would implement it:**  
For CI/CD, I would store Snowflake credentials in GitHub Actions Secrets. For a deployed Streamlit dashboard, I would use Streamlit’s secrets management or the hosting platform’s secret store. Of course GitHub supports encrypted secrets at repository, environment, and organization levels, and Streamlit supports secrets for deployed apps so credentials stay outside the codebase, so this would be easily implemented in a more production-style environment.

---

### Automated deployment for dbt and the dashboard

This version is run manually from a local machine (obviously). In production, code changes should be tested and deployed in a controlled way.

**Rationale:** Of course, manual deployment is easy to mess up. Automated deployment makes changes repeatable and easier to review.

**Possible tools:** GitHub Actions, dbt Cloud jobs, Docker, Streamlit Community Cloud, Snowflake CLI, CI/CD pipelines.

**How I would implement it:**  
I would add a GitHub Actions workflow that runs Python tests, runs dbt compile, and runs dbt tests before changes are merged. After approval, a deployment job could run dbt models against the production environment. The Streamlit dashboard could be deployed through Streamlit Community Cloud or another hosting platform with secrets stored outside the repo.

---

### More robust anomaly detection for unusual returns

This project uses rule-based logic, such as late returns, no-receipt returns, damaged items, and high-value returns. In production, unusual patterns could be more complex.

**Rationale:** Return abuse or operational issues may not always follow simple rules. A store or product could look normal alone but unusual compared with its history or peer group.

**Possible tools:** SQL anomaly rules, Python, scikit-learn, Snowflake ML, scheduled scoring jobs, perhaps using isolation forest, z-score checks, rolling averages (as used in my capstone project).

**How I would implement it:**  
I would start with interpretable SQL checks, such as return rates above a rolling 30-day average or stores above peer-group thresholds. And If needed I would add a simple anomaly model using Python or Snowflake ML to flag unusual store/product/customer return patterns. I would still keep the output explainable so analysts can see why something was flagged.

---

### Separate development, staging, and production environments

This project uses one Snowflake database. In production, development work should be separated from tested and business-facing data.

**Rationale:** Developers need a safe place to test changes without breaking dashboards used by business teams.

**Possible tools:** Separate Snowflake databases or schemas, dbt targets, Git branches, GitHub Actions environments.

**How I would implement it:**  
I would create separate environments such as `RETAIL_RETURNS_DEV`, `RETAIL_RETURNS_STAGING`, and `RETAIL_RETURNS_PROD`. dbt targets would point to the correct environment. Pull requests would run against dev or staging first, and only approved changes would be deployed to production. GitHub Actions environments can also store separate secrets for each environment.