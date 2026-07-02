from pathlib import Path

import pandas as pd

from data_generator.generate_data import generate_all_data


EXPECTED_COLUMNS = {
    "products": [
        "product_id",
        "product_name",
        "product_category",
        "product_subcategory",
        "brand",
        "unit_price",
        "cost",
        "active_flag",
    ],
    "stores": [
        "store_id",
        "store_name",
        "city",
        "province",
        "region",
        "store_type",
        "open_date",
    ],
    "customers": [
        "customer_id",
        "loyalty_tier",
        "signup_date",
        "city",
        "province",
    ],
    "employees": [
        "employee_id",
        "store_id",
        "role",
        "hire_date",
        "active_flag",
    ],
    "sales": [
        "sale_id",
        "transaction_id",
        "sale_date",
        "store_id",
        "customer_id",
        "employee_id",
        "product_id",
        "quantity",
        "unit_price",
        "discount_amount",
        "sale_amount",
        "payment_method",
        "sales_channel",
    ],
    "returns": [
        "return_id",
        "sale_id",
        "transaction_id",
        "return_date",
        "store_id",
        "customer_id",
        "employee_id",
        "product_id",
        "return_quantity",
        "return_amount",
        "return_reason",
        "return_channel",
        "refund_method",
        "receipt_present",
        "item_condition",
        "policy_exception_flag",
    ],
}


def test_generator_creates_expected_csvs_and_columns(tmp_path: Path) -> None:
    counts = {
        "products": 25,
        "stores": 5,
        "customers": 40,
        "employees": 15,
        "sales": 150,
        "returns": 30,
    }

    generate_all_data(tmp_path, counts=counts, seed=123)

    for dataset_name, expected_columns in EXPECTED_COLUMNS.items():
        csv_path = tmp_path / f"{dataset_name}.csv"
        assert csv_path.exists()

        frame = pd.read_csv(csv_path)
        assert list(frame.columns) == expected_columns
        assert len(frame) == counts[dataset_name]


def test_returns_reference_sales_and_respect_sale_dates(tmp_path: Path) -> None:
    generate_all_data(
        tmp_path,
        counts={
            "products": 20,
            "stores": 4,
            "customers": 35,
            "employees": 12,
            "sales": 120,
            "returns": 25,
        },
        seed=456,
    )

    sales = pd.read_csv(tmp_path / "sales.csv")
    returns = pd.read_csv(tmp_path / "returns.csv")

    assert set(returns["sale_id"]).issubset(set(sales["sale_id"]))

    sale_dates = sales[["sale_id", "sale_date"]]
    merged = returns.merge(sale_dates, on="sale_id", how="left")
    assert pd.to_datetime(merged["return_date"]).ge(pd.to_datetime(merged["sale_date"])).all()


def test_generated_amounts_are_not_negative(tmp_path: Path) -> None:
    generate_all_data(
        tmp_path,
        counts={
            "products": 15,
            "stores": 3,
            "customers": 25,
            "employees": 9,
            "sales": 100,
            "returns": 20,
        },
        seed=789,
    )

    sales = pd.read_csv(tmp_path / "sales.csv")
    returns = pd.read_csv(tmp_path / "returns.csv")

    assert sales["sale_amount"].ge(0).all()
    assert returns["return_amount"].ge(0).all()


def test_customer_data_is_non_identifying(tmp_path: Path) -> None:
    generate_all_data(
        tmp_path,
        counts={
            "products": 10,
            "stores": 3,
            "customers": 12,
            "employees": 8,
            "sales": 50,
            "returns": 10,
        },
        seed=101,
    )

    customers = pd.read_csv(tmp_path / "customers.csv")
    forbidden_tokens = ["name", "email", "phone", "address"]

    for column in customers.columns:
        assert not any(token in column.lower() for token in forbidden_tokens)

    assert list(customers.columns) == EXPECTED_COLUMNS["customers"]
