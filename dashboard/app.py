import os
import re
from typing import Iterable

import pandas as pd
import plotly.express as px
import snowflake.connector
import streamlit as st

try:
    from dotenv import load_dotenv

    # load local env vars when a .env file exists
    load_dotenv()
except ImportError:
    pass


# env vars the app needs before it can talk to snowflake
REQUIRED_ENV_VARS = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
]

# final mart tables used by each dashboard section
MART_TABLES = {
    "daily": "MART_DAILY_SALES_RETURNS_SUMMARY",
    "product": "MART_RETURN_RATE_BY_PRODUCT",
    "store": "MART_RETURN_RATE_BY_STORE",
    "reason": "MART_RETURN_REASON_SUMMARY",
    "exceptions": "MART_RETURN_POLICY_EXCEPTIONS",
    "employee": "MART_EMPLOYEE_RETURN_ACTIVITY",
}


st.set_page_config(
    page_title="Retail Returns Analytics",
    page_icon=":bar_chart:",
    layout="wide",
)


def get_missing_env_vars() -> list[str]:
    return [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]


def get_snowflake_config() -> dict[str, str]:
    return {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "password": os.environ["SNOWFLAKE_PASSWORD"],
        "role": os.environ["SNOWFLAKE_ROLE"],
        "warehouse": os.environ["SNOWFLAKE_WAREHOUSE"],
        "database": os.environ["SNOWFLAKE_DATABASE"],
        "schema": os.environ["SNOWFLAKE_SCHEMA"],
    }


def normalize_identifier(identifier: str) -> str:
    """allow simple snowflake identifiers while avoiding accidental sql injection."""
    clean_identifier = identifier.strip().upper()
    if not re.fullmatch(r"[A-Z0-9_$]+", clean_identifier):
        raise ValueError(f"Unsupported Snowflake identifier: {identifier}")
    return clean_identifier


def mart_table(table_name: str) -> str:
    database = normalize_identifier(os.environ["SNOWFLAKE_DATABASE"])
    schema = normalize_identifier(os.environ["SNOWFLAKE_SCHEMA"])
    table = normalize_identifier(table_name)
    return f"{database}.{schema}.{table}"


@st.cache_data(ttl=600, show_spinner=False)
def run_query(sql: str) -> pd.DataFrame:
    # cache snowflake reads so tab changes do not rerun every query
    conn = snowflake.connector.connect(**get_snowflake_config())
    try:
        frame = pd.read_sql(sql, conn)
    finally:
        conn.close()

    return normalize_dataframe(frame)


def normalize_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    # snowflake often returns uppercase columns; charts use lowercase names
    frame = frame.copy()
    frame.columns = [str(column).strip().strip('"').lower() for column in frame.columns]
    return frame


def as_bool_series(series: pd.Series) -> pd.Series:
    # booleans can come back as true/false strings, depending on the query path
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)

    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "t", "yes", "y", "1"])
    )


def show_table(frame: pd.DataFrame, columns: list[str], *, max_rows: int | None = None) -> None:
    # show useful context instead of crashing when a mart shape changes
    missing_columns = [column for column in columns if column not in frame.columns]
    if missing_columns:
        st.warning("This table is missing expected columns.")
        st.write("Missing columns:", missing_columns)
        st.write("Available columns:", list(frame.columns))
        st.dataframe(frame.head(max_rows), use_container_width=True, hide_index=True)
        return

    display_frame = frame[columns]
    if max_rows is not None:
        display_frame = display_frame.head(max_rows)

    st.dataframe(display_frame, use_container_width=True, hide_index=True)


def load_mart_data() -> dict[str, pd.DataFrame]:
    # keep dashboard queries simple; the business logic lives in dbt marts
    return {
        "daily": run_query(
            f"""
            select *
            from {mart_table(MART_TABLES["daily"])}
            order by calendar_date
            """
        ),
        "product": run_query(
            f"""
            select *
            from {mart_table(MART_TABLES["product"])}
            order by return_rate desc, total_return_amount desc
            """
        ),
        "store": run_query(
            f"""
            select *
            from {mart_table(MART_TABLES["store"])}
            order by return_rate desc, total_return_amount desc
            """
        ),
        "reason": run_query(
            f"""
            select *
            from {mart_table(MART_TABLES["reason"])}
            order by total_returns desc
            """
        ),
        "exceptions": run_query(
            f"""
            select *
            from {mart_table(MART_TABLES["exceptions"])}
            order by return_date desc, return_amount desc
            """
        ),
        "employee": run_query(
            f"""
            select *
            from {mart_table(MART_TABLES["employee"])}
            order by unusual_return_activity_flag desc, total_returns_processed desc
            """
        ),
    }


def money(value: float) -> str:
    # small display helpers for kpi cards
    return f"${value:,.0f}"


def number(value: float) -> str:
    return f"{value:,.0f}"


def percent(value: float) -> str:
    return f"{value:.1%}"


def add_product_label(frame: pd.DataFrame) -> pd.DataFrame:
    # use product names for charts, with ids as a fallback
    frame = frame.copy()
    frame["product_label"] = frame["product_name"].fillna(frame["product_id"])
    return frame


def render_metric_cards(daily: pd.DataFrame) -> None:
    total_sales = daily["total_sales"].sum()
    total_sales_amount = daily["total_sales_amount"].sum()
    total_returns = daily["total_returns"].sum()
    total_return_amount = daily["total_return_amount"].sum()
    overall_return_rate = total_returns / total_sales if total_sales else 0
    net_revenue = daily["net_revenue_after_returns"].sum()

    first_row = st.columns(3)
    first_row[0].metric("Total sales", number(total_sales))
    first_row[1].metric("Total sales amount", money(total_sales_amount))
    first_row[2].metric("Net revenue after returns", money(net_revenue))

    second_row = st.columns(3)
    second_row[0].metric("Total returns", number(total_returns))
    second_row[1].metric("Total return amount", money(total_return_amount))
    second_row[2].metric("Overall return rate", percent(overall_return_rate))


def render_daily_trends(daily: pd.DataFrame) -> None:
    st.header("Daily Trends")

    trend_frame = daily.copy()
    trend_frame["calendar_date"] = pd.to_datetime(trend_frame["calendar_date"])

    amount_chart = px.line(
        trend_frame,
        x="calendar_date",
        y=["total_sales_amount", "total_return_amount"],
        labels={"value": "Amount", "calendar_date": "Date", "variable": "Metric"},
        title="Daily Sales and Return Amount",
    )

    rate_chart = px.line(
        trend_frame,
        x="calendar_date",
        y="return_rate",
        labels={"return_rate": "Return rate", "calendar_date": "Date"},
        title="Daily Return Rate",
    )
    rate_chart.update_yaxes(tickformat=".1%")

    left, right = st.columns([2, 1])
    left.plotly_chart(amount_chart, use_container_width=True)
    right.plotly_chart(rate_chart, use_container_width=True)


def render_product_returns(products: pd.DataFrame) -> None:
    st.header("Product Returns")

    products = normalize_dataframe(products)
    required_columns = [
        "product_id",
        "product_name",
        "product_category",
        "total_units_sold",
        "total_units_returned",
        "return_rate",
        "total_return_amount",
        "top_return_reason",
        "high_return_product_flag",
    ]
    missing_columns = [column for column in required_columns if column not in products.columns]
    if missing_columns:
        st.error("Product mart data is missing columns needed by this section.")
        st.write("Missing columns:", missing_columns)
        st.write("Available columns:", list(products.columns))
        st.stop()

    product_frame = add_product_label(products)
    product_frame["high_return_product_flag"] = as_bool_series(product_frame["high_return_product_flag"])
    highest_rate = product_frame.sort_values(
        ["return_rate", "total_units_sold"],
        ascending=[False, False],
    ).head(10)
    highest_amount = product_frame.sort_values("total_return_amount", ascending=False).head(10)
    high_return_products = product_frame[product_frame["high_return_product_flag"]].copy()

    left, right = st.columns(2)

    rate_chart = px.bar(
        highest_rate.sort_values("return_rate"),
        x="return_rate",
        y="product_label",
        orientation="h",
        labels={"return_rate": "Return rate", "product_label": "Product"},
        title="Top 10 Products by Return Rate",
    )
    rate_chart.update_xaxes(tickformat=".1%")
    left.plotly_chart(rate_chart, use_container_width=True)

    amount_chart = px.bar(
        highest_amount.sort_values("total_return_amount"),
        x="total_return_amount",
        y="product_label",
        orientation="h",
        labels={"total_return_amount": "Return amount", "product_label": "Product"},
        title="Top 10 Products by Return Amount",
    )
    right.plotly_chart(amount_chart, use_container_width=True)

    st.subheader("High-Return Products")
    show_table(
        high_return_products,
        [
            "product_id",
            "product_name",
            "product_category",
            "total_units_sold",
            "total_units_returned",
            "return_rate",
            "total_return_amount",
            "top_return_reason",
        ],
    )


def render_store_returns(stores: pd.DataFrame) -> None:
    st.header("Store Returns")

    stores = normalize_dataframe(stores)
    store_frame = stores.copy()
    store_frame["store_label"] = store_frame["store_name"].fillna(store_frame["store_id"])
    rate_columns = ["return_rate", "policy_exception_rate", "no_receipt_return_rate"]
    rate_frame = store_frame.melt(
        id_vars=["store_label"],
        value_vars=rate_columns,
        var_name="metric",
        value_name="rate",
    )
    rate_frame["metric"] = rate_frame["metric"].replace(
        {
            "return_rate": "Return rate",
            "policy_exception_rate": "Policy exception rate",
            "no_receipt_return_rate": "No-receipt return rate",
        }
    )

    rate_chart = px.bar(
        rate_frame,
        x="store_label",
        y="rate",
        color="metric",
        barmode="group",
        labels={"store_label": "Store", "rate": "Rate", "metric": "Metric"},
        title="Return, Policy Exception, and No-Receipt Rates by Store",
    )
    rate_chart.update_yaxes(tickformat=".1%")
    rate_chart.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(rate_chart, use_container_width=True)

    show_table(
        store_frame,
        [
            "store_id",
            "store_name",
            "store_city",
            "store_region",
            "total_sales",
            "total_returns",
            "return_rate",
            "policy_exception_rate",
            "no_receipt_return_rate",
        ],
    )


def render_return_reasons(reasons: pd.DataFrame) -> None:
    st.header("Return Reasons")

    left, middle, right = st.columns(3)

    returns_chart = px.bar(
        reasons,
        x="return_reason",
        y="total_returns",
        labels={"return_reason": "Return reason", "total_returns": "Returns"},
        title="Total Returns by Reason",
    )
    left.plotly_chart(returns_chart, use_container_width=True)

    amount_chart = px.bar(
        reasons,
        x="return_reason",
        y="total_return_amount",
        labels={"return_reason": "Return reason", "total_return_amount": "Return amount"},
        title="Return Amount by Reason",
    )
    middle.plotly_chart(amount_chart, use_container_width=True)

    percent_chart = px.pie(
        reasons,
        names="return_reason",
        values="percent_of_returns",
        title="Percent of Returns by Reason",
    )
    right.plotly_chart(percent_chart, use_container_width=True)

    st.dataframe(reasons, use_container_width=True, hide_index=True)


def split_exception_reasons(values: Iterable[str]) -> list[str]:
    reasons: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        reasons.update(reason.strip() for reason in value.split(",") if reason.strip())
    return sorted(reasons)


def render_policy_exceptions(exceptions: pd.DataFrame) -> None:
    st.header("Policy Exceptions")

    exceptions = normalize_dataframe(exceptions)
    if exceptions.empty:
        st.info("No policy exception returns found.")
        return

    filter_row = st.columns(3)
    selected_reasons = filter_row[0].multiselect(
        "Return reason",
        sorted(exceptions["return_reason"].dropna().unique()),
    )
    selected_stores = filter_row[1].multiselect(
        "Store",
        sorted(exceptions["store_name"].dropna().unique()),
    )
    exception_types = split_exception_reasons(exceptions["exception_reason"])
    selected_exception_types = filter_row[2].multiselect("Exception type", exception_types)

    filtered = exceptions.copy()
    if selected_reasons:
        filtered = filtered[filtered["return_reason"].isin(selected_reasons)]
    if selected_stores:
        filtered = filtered[filtered["store_name"].isin(selected_stores)]
    if selected_exception_types:
        mask = pd.Series(False, index=filtered.index)
        for exception_type in selected_exception_types:
            mask = mask | filtered["exception_reason"].str.contains(exception_type, regex=False, na=False)
        filtered = filtered[mask]

    expanded = filtered.assign(
        exception_type=filtered["exception_reason"].str.split(", ")
    ).explode("exception_type")
    exception_counts = (
        expanded.groupby("exception_type", dropna=True)
        .size()
        .reset_index(name="return_count")
        .sort_values("return_count", ascending=False)
    )

    left, right = st.columns([1, 2])
    count_chart = px.bar(
        exception_counts,
        x="exception_type",
        y="return_count",
        labels={"exception_type": "Exception type", "return_count": "Returns"},
        title="Policy Exception Count by Type",
    )
    left.plotly_chart(count_chart, use_container_width=True)

    right.metric("Filtered exception returns", number(len(filtered)))
    right.metric("Filtered return amount", money(filtered["return_amount"].sum()))

    show_table(
        filtered,
        [
            "return_id",
            "return_date",
            "store_name",
            "product_name",
            "customer_loyalty_tier",
            "employee_id",
            "return_reason",
            "return_amount",
            "days_until_return",
            "exception_reason",
        ],
        max_rows=500,
    )


def render_employee_activity(employees: pd.DataFrame) -> None:
    st.header("Employee Return Activity")

    employees = normalize_dataframe(employees)
    employee_frame = employees.copy()
    employee_frame["unusual_return_activity_flag"] = as_bool_series(
        employee_frame["unusual_return_activity_flag"]
    )
    unusual = employee_frame[employee_frame["unusual_return_activity_flag"]].copy()
    top_returns = employee_frame.sort_values("total_returns_processed", ascending=False).head(15)

    left, right = st.columns(2)

    returns_chart = px.bar(
        top_returns.sort_values("total_returns_processed"),
        x="total_returns_processed",
        y="employee_id",
        orientation="h",
        color="unusual_return_activity_flag",
        labels={"total_returns_processed": "Returns processed", "employee_id": "Employee"},
        title="Top Employees by Returns Processed",
    )
    left.plotly_chart(returns_chart, use_container_width=True)

    exception_chart = px.scatter(
        employee_frame,
        x="total_returns_processed",
        y="policy_exception_returns_processed",
        size="no_receipt_returns_processed",
        color="unusual_return_activity_flag",
        hover_data=["employee_id", "employee_role", "average_return_amount"],
        labels={
            "total_returns_processed": "Returns processed",
            "policy_exception_returns_processed": "Policy exception returns",
        },
        title="Employee Policy Exception Activity",
    )
    right.plotly_chart(exception_chart, use_container_width=True)

    st.subheader("Employees with Unusual Return Activity")
    show_table(
        unusual,
        [
            "employee_id",
            "store_id",
            "employee_role",
            "total_returns_processed",
            "total_return_amount_processed",
            "policy_exception_returns_processed",
            "no_receipt_returns_processed",
            "average_return_amount",
        ],
    )


def main() -> None:
    # validate config first, then load marts and render each dashboard section
    st.title("Retail Returns Analytics")
    st.caption("Business-ready reporting powered by Snowflake marts and dbt transformations.")

    missing_env_vars = get_missing_env_vars()
    if missing_env_vars:
        st.error("Missing Snowflake environment variables.")
        st.write("Set these values before running the dashboard:")
        st.code("\n".join(missing_env_vars))
        st.info("Use `.env.example` as a local template. Do not commit real credentials.")
        st.stop()

    with st.spinner("Loading mart data from Snowflake..."):
        try:
            data = load_mart_data()
        except Exception as exc:
            st.error("Could not load data from Snowflake.")
            st.exception(exc)
            st.stop()

    st.header("Overview")
    render_metric_cards(data["daily"])

    tabs = st.tabs(
        [
            "Daily Trends",
            "Product Returns",
            "Store Returns",
            "Return Reasons",
            "Policy Exceptions",
            "Employee Activity",
        ]
    )

    with tabs[0]:
        render_daily_trends(data["daily"])
    with tabs[1]:
        render_product_returns(data["product"])
    with tabs[2]:
        render_store_returns(data["store"])
    with tabs[3]:
        render_return_reasons(data["reason"])
    with tabs[4]:
        render_policy_exceptions(data["exceptions"])
    with tabs[5]:
        render_employee_activity(data["employee"])


if __name__ == "__main__":
    main()
