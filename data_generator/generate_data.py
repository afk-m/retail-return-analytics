from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

try:
    from .config import (
        BRANDS,
        CUSTOMER_SIGNUP_START_DATE,
        DEFAULT_COUNTS,
        DEFAULT_OUTPUT_DIR,
        EMPLOYEE_HIRE_START_DATE,
        EMPLOYEE_ROLES,
        ITEM_CONDITIONS,
        LOYALTY_TIERS,
        ONTARIO_LOCATIONS,
        PAYMENT_METHODS,
        PRODUCT_CATALOG,
        RANDOM_SEED,
        RETURN_CHANNELS,
        RETURN_REASONS,
        SALES_CHANNELS,
        SALES_END_DATE,
        SALES_START_DATE,
        STORE_OPEN_START_DATE,
        STORE_TYPES,
    )
except ImportError:  # Allows `python data_generator/generate_data.py`.
    from config import (
        BRANDS,
        CUSTOMER_SIGNUP_START_DATE,
        DEFAULT_COUNTS,
        DEFAULT_OUTPUT_DIR,
        EMPLOYEE_HIRE_START_DATE,
        EMPLOYEE_ROLES,
        ITEM_CONDITIONS,
        LOYALTY_TIERS,
        ONTARIO_LOCATIONS,
        PAYMENT_METHODS,
        PRODUCT_CATALOG,
        RANDOM_SEED,
        RETURN_CHANNELS,
        RETURN_REASONS,
        SALES_CHANNELS,
        SALES_END_DATE,
        SALES_START_DATE,
        STORE_OPEN_START_DATE,
        STORE_TYPES,
    )


CSV_ORDER = [
    "sales",
    "returns",
    "products",
    "stores",
    "customers",
    "employees",
]


def _date_series(rng: np.random.Generator, count: int, start: date, end: date) -> list[str]:
    days = (end - start).days
    offsets = rng.integers(0, days + 1, size=count)
    return [(start + timedelta(days=int(offset))).isoformat() for offset in offsets]


def _weighted_choice(
    rng: np.random.Generator,
    values: pd.Series | list[str] | np.ndarray,
    size: int,
    probabilities: list[float] | np.ndarray | None = None,
) -> np.ndarray:
    return rng.choice(np.asarray(values), size=size, replace=True, p=probabilities)


def _normalise(weights: np.ndarray) -> np.ndarray:
    clean_weights = np.asarray(weights, dtype=float)
    return clean_weights / clean_weights.sum()


def _money(values: pd.Series | np.ndarray | float) -> pd.Series | np.ndarray | float:
    return np.round(values, 2)


def generate_products(
    count: int,
    rng: np.random.Generator,
    fake: Faker,
) -> pd.DataFrame:
    categories = list(PRODUCT_CATALOG.keys())
    category_weights = _normalise(np.array([1.35, 0.8, 1.05, 0.75, 1.25, 0.65]))

    rows = []
    for product_number in range(1, count + 1):
        category = rng.choice(categories, p=category_weights)
        subcategory = rng.choice(PRODUCT_CATALOG[category])
        brand = rng.choice(BRANDS)
        descriptor = fake.word().replace("-", "_")

        if category == "electronics":
            unit_price = rng.lognormal(mean=4.6, sigma=0.7)
        elif category == "sporting_goods":
            unit_price = rng.lognormal(mean=4.1, sigma=0.55)
        elif category == "home":
            unit_price = rng.lognormal(mean=3.7, sigma=0.5)
        elif category == "apparel":
            unit_price = rng.lognormal(mean=3.5, sigma=0.45)
        elif category == "beauty":
            unit_price = rng.lognormal(mean=3.25, sigma=0.4)
        else:
            unit_price = rng.lognormal(mean=2.75, sigma=0.45)

        unit_price = float(np.clip(unit_price, 4.99, 1299.99))
        cost = unit_price * rng.uniform(0.42, 0.72)

        rows.append(
            {
                "product_id": f"P{product_number:06d}",
                "product_name": f"{brand} {subcategory.replace('_', ' ')} {descriptor}".title(),
                "product_category": category,
                "product_subcategory": subcategory,
                "brand": brand,
                "unit_price": _money(unit_price),
                "cost": _money(cost),
                "active_flag": bool(rng.random() < 0.96),
            }
        )

    return pd.DataFrame(rows)


def generate_stores(count: int, rng: np.random.Generator) -> pd.DataFrame:
    location_indexes = rng.choice(
        len(ONTARIO_LOCATIONS),
        size=count,
        replace=count > len(ONTARIO_LOCATIONS),
    )

    rows = []
    for store_number, location_index in enumerate(location_indexes, start=1):
        city, province, region = ONTARIO_LOCATIONS[int(location_index)]
        store_type = rng.choice(STORE_TYPES, p=[0.1, 0.35, 0.15, 0.3, 0.1])
        rows.append(
            {
                "store_id": f"S{store_number:03d}",
                "store_name": f"{city} {store_type.replace('_', ' ').title()}",
                "city": city,
                "province": province,
                "region": region,
                "store_type": store_type,
                "open_date": _date_series(
                    rng,
                    1,
                    STORE_OPEN_START_DATE,
                    SALES_START_DATE - timedelta(days=90),
                )[0],
            }
        )

    return pd.DataFrame(rows)


def generate_customers(count: int, rng: np.random.Generator) -> pd.DataFrame:
    location_indexes = rng.choice(len(ONTARIO_LOCATIONS), size=count, replace=True)
    cities = [ONTARIO_LOCATIONS[int(index)][0] for index in location_indexes]
    provinces = [ONTARIO_LOCATIONS[int(index)][1] for index in location_indexes]

    return pd.DataFrame(
        {
            "customer_id": [f"C{customer_number:07d}" for customer_number in range(1, count + 1)],
            "loyalty_tier": _weighted_choice(
                rng,
                LOYALTY_TIERS,
                count,
                probabilities=[0.28, 0.32, 0.22, 0.14, 0.04],
            ),
            "signup_date": _date_series(
                rng,
                count,
                CUSTOMER_SIGNUP_START_DATE,
                SALES_END_DATE,
            ),
            "city": cities,
            "province": provinces,
        }
    )


def generate_employees(
    count: int,
    stores: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    if stores.empty:
        raise ValueError("At least one store is required to generate employees.")

    store_ids = stores["store_id"].to_numpy()
    assignments = np.resize(store_ids, count)
    rng.shuffle(assignments)

    rows = []
    for employee_number, store_id in enumerate(assignments, start=1):
        rows.append(
            {
                "employee_id": f"E{employee_number:05d}",
                "store_id": store_id,
                "role": rng.choice(
                    EMPLOYEE_ROLES,
                    p=[0.34, 0.22, 0.13, 0.08, 0.11, 0.08, 0.04],
                ),
                "hire_date": _date_series(
                    rng,
                    1,
                    EMPLOYEE_HIRE_START_DATE,
                    SALES_END_DATE,
                )[0],
                "active_flag": bool(rng.random() < 0.9),
            }
        )

    return pd.DataFrame(rows)


def _employee_ids_for_store(employees: pd.DataFrame) -> dict[str, np.ndarray]:
    grouped = employees.groupby("store_id")["employee_id"].apply(lambda values: values.to_numpy())
    return grouped.to_dict()


def _choose_sales_employee_ids(
    rng: np.random.Generator,
    store_ids: np.ndarray,
    employees: pd.DataFrame,
) -> list[str]:
    employee_lookup = _employee_ids_for_store(employees)
    all_employee_ids = employees["employee_id"].to_numpy()

    selected = []
    for store_id in store_ids:
        candidates = employee_lookup.get(store_id, all_employee_ids)
        selected.append(str(rng.choice(candidates)))
    return selected


def _product_sales_probabilities(products: pd.DataFrame) -> np.ndarray:
    category_weights = {
        "apparel": 1.25,
        "electronics": 0.62,
        "home": 0.95,
        "beauty": 0.9,
        "grocery": 1.45,
        "sporting_goods": 0.55,
    }
    weights = products["product_category"].map(category_weights).to_numpy(dtype=float, copy=True)
    weights *= np.where(products["active_flag"].to_numpy(dtype=bool), 1.0, 0.15)
    weights *= 1 / np.sqrt(products["unit_price"].to_numpy(dtype=float))
    return _normalise(weights)


def generate_sales(
    count: int,
    products: pd.DataFrame,
    stores: pd.DataFrame,
    customers: pd.DataFrame,
    employees: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    if any(frame.empty for frame in [products, stores, customers, employees]):
        raise ValueError("Products, stores, customers, and employees are required to generate sales.")

    product_ids = _weighted_choice(
        rng,
        products["product_id"],
        count,
        probabilities=_product_sales_probabilities(products),
    )
    product_prices = products.set_index("product_id")["unit_price"]
    unit_prices = product_prices.loc[product_ids].to_numpy(dtype=float)

    store_weights = _normalise(rng.lognormal(mean=0, sigma=0.45, size=len(stores)))
    store_ids = _weighted_choice(rng, stores["store_id"], count, probabilities=store_weights)
    employee_ids = _choose_sales_employee_ids(rng, store_ids, employees)

    quantities = rng.choice(np.array([1, 2, 3, 4, 5]), size=count, p=[0.68, 0.19, 0.08, 0.035, 0.015])
    gross_amounts = unit_prices * quantities
    discount_rates = rng.choice(
        np.array([0.0, 0.05, 0.10, 0.15, 0.20, 0.30]),
        size=count,
        p=[0.55, 0.16, 0.13, 0.08, 0.06, 0.02],
    )
    discount_amounts = _money(gross_amounts * discount_rates)
    sale_amounts = _money(np.maximum(gross_amounts - discount_amounts, 0))

    return pd.DataFrame(
        {
            "sale_id": [f"SL{sale_number:08d}" for sale_number in range(1, count + 1)],
            "transaction_id": [f"TXN{transaction_number:09d}" for transaction_number in range(1, count + 1)],
            "sale_date": _date_series(rng, count, SALES_START_DATE, SALES_END_DATE),
            "store_id": store_ids,
            "customer_id": _weighted_choice(rng, customers["customer_id"], count),
            "employee_id": employee_ids,
            "product_id": product_ids,
            "quantity": quantities,
            "unit_price": _money(unit_prices),
            "discount_amount": discount_amounts,
            "sale_amount": sale_amounts,
            "payment_method": _weighted_choice(
                rng,
                PAYMENT_METHODS,
                count,
                probabilities=[0.48, 0.28, 0.12, 0.08, 0.04],
            ),
            "sales_channel": _weighted_choice(
                rng,
                SALES_CHANNELS,
                count,
                probabilities=[0.7, 0.24, 0.06],
            ),
        }
    )


def _product_return_multipliers(products: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    category_multipliers = {
        "apparel": 1.45,
        "electronics": 1.55,
        "home": 0.9,
        "beauty": 0.82,
        "grocery": 0.32,
        "sporting_goods": 1.05,
    }
    multipliers = products["product_category"].map(category_multipliers).astype(float)

    high_rate_count = max(1, int(len(products) * 0.08))
    high_rate_product_indexes = rng.choice(products.index, size=high_rate_count, replace=False)
    multipliers.loc[high_rate_product_indexes] *= rng.uniform(2.2, 5.0, size=high_rate_count)
    return pd.Series(multipliers.to_numpy(), index=products["product_id"])


def _store_return_multipliers(stores: pd.DataFrame, rng: np.random.Generator) -> pd.Series:
    multipliers = pd.Series(rng.lognormal(mean=0, sigma=0.35, size=len(stores)), index=stores["store_id"])

    high_volume_count = max(1, int(len(stores) * 0.2))
    high_volume_stores = rng.choice(multipliers.index, size=high_volume_count, replace=False)
    multipliers.loc[high_volume_stores] *= rng.uniform(1.8, 3.5, size=high_volume_count)
    return multipliers


def _return_employee_weights(employees: pd.DataFrame, rng: np.random.Generator) -> dict[str, pd.Series]:
    weights_by_store: dict[str, pd.Series] = {}

    for store_id, group in employees.groupby("store_id"):
        weights = pd.Series(rng.lognormal(mean=0, sigma=0.55, size=len(group)), index=group["employee_id"])
        specialist_mask = group.set_index("employee_id")["role"].isin(["returns_specialist", "customer_service"])
        weights.loc[specialist_mask] *= 2.0

        high_processor_count = max(1, int(len(group) * 0.15))
        high_processors = rng.choice(weights.index, size=high_processor_count, replace=False)
        weights.loc[high_processors] *= rng.uniform(2.0, 4.5, size=high_processor_count)
        weights_by_store[store_id] = weights / weights.sum()

    return weights_by_store


def _choose_return_employee_id(
    rng: np.random.Generator,
    store_id: str,
    employee_weights: dict[str, pd.Series],
    employees: pd.DataFrame,
) -> str:
    weights = employee_weights.get(store_id)
    if weights is None or weights.empty:
        return str(rng.choice(employees["employee_id"]))
    return str(rng.choice(weights.index.to_numpy(), p=weights.to_numpy(dtype=float)))


def _choose_return_reason(rng: np.random.Generator, sale_channel: str) -> str:
    if sale_channel == "online":
        probabilities = [0.25, 0.18, 0.12, 0.08, 0.16, 0.08, 0.09, 0.04]
    else:
        probabilities = [0.32, 0.22, 0.12, 0.09, 0.08, 0.09, 0.02, 0.06]
    return str(rng.choice(RETURN_REASONS, p=probabilities))


def _choose_item_condition(rng: np.random.Generator, return_reason: str) -> str:
    if return_reason == "defective":
        return str(rng.choice(ITEM_CONDITIONS, p=[0.03, 0.18, 0.08, 0.65, 0.06]))
    if return_reason == "damaged":
        return str(rng.choice(ITEM_CONDITIONS, p=[0.02, 0.12, 0.72, 0.08, 0.06]))
    return str(rng.choice(ITEM_CONDITIONS, p=[0.38, 0.41, 0.06, 0.04, 0.11]))


def _choose_return_channel(rng: np.random.Generator, sale_channel: str) -> str:
    if sale_channel == "online":
        return str(rng.choice(RETURN_CHANNELS, p=[0.42, 0.5, 0.08]))
    if sale_channel == "curbside_pickup":
        return str(rng.choice(RETURN_CHANNELS, p=[0.5, 0.12, 0.38]))
    return str(rng.choice(RETURN_CHANNELS, p=[0.9, 0.05, 0.05]))


def _choose_refund_method(
    rng: np.random.Generator,
    payment_method: str,
    receipt_present: bool,
    late_return: bool,
    high_value_return: bool,
) -> str:
    if not receipt_present or late_return or high_value_return:
        return str(rng.choice(["store_credit", payment_method], p=[0.62, 0.38]))
    if payment_method == "cash":
        return str(rng.choice(["cash", "store_credit"], p=[0.82, 0.18]))
    return str(rng.choice([payment_method, "store_credit"], p=[0.93, 0.07]))


def generate_returns(
    count: int,
    sales: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
    employees: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    if sales.empty:
        raise ValueError("At least one sale is required to generate returns.")

    return_count = min(count, len(sales))
    product_multipliers = _product_return_multipliers(products, rng)
    store_multipliers = _store_return_multipliers(stores, rng)

    sale_amounts = sales["sale_amount"].to_numpy(dtype=float)
    high_value_floor = max(150.0, float(np.quantile(sale_amounts, 0.9)))
    selection_weights = np.ones(len(sales), dtype=float)
    selection_weights *= sales["product_id"].map(product_multipliers).to_numpy(dtype=float)
    selection_weights *= sales["store_id"].map(store_multipliers).to_numpy(dtype=float)
    selection_weights *= np.where(sales["sales_channel"].eq("online"), 1.55, 1.0)
    selection_weights *= np.where(sale_amounts >= high_value_floor, 2.75, 1.0)

    selected_positions = rng.choice(
        sales.index.to_numpy(),
        size=return_count,
        replace=False,
        p=_normalise(selection_weights),
    )
    returned_sales = sales.loc[selected_positions].reset_index(drop=True)

    employee_weights = _return_employee_weights(employees, rng)
    high_value_threshold = max(200.0, float(np.quantile(returned_sales["sale_amount"], 0.92)))

    rows = []
    for return_number, sale in enumerate(returned_sales.itertuples(index=False), start=1):
        sale_date = date.fromisoformat(sale.sale_date)
        late_return = bool(rng.random() < 0.13)
        if late_return:
            return_delay = int(rng.integers(31, 121))
        else:
            return_delay = int(rng.choice(np.arange(0, 31), p=_normalise(np.linspace(1.9, 0.35, 31))))

        return_date = sale_date + timedelta(days=return_delay)
        return_quantity = int(rng.integers(1, int(sale.quantity) + 1))
        return_amount = float(_money((float(sale.sale_amount) / int(sale.quantity)) * return_quantity))
        high_value_return = return_amount >= high_value_threshold
        receipt_present = bool(rng.random() >= (0.12 + (0.08 if late_return else 0.0)))
        return_reason = _choose_return_reason(rng, str(sale.sales_channel))
        item_condition = _choose_item_condition(rng, return_reason)
        refund_method = _choose_refund_method(
            rng,
            str(sale.payment_method),
            receipt_present,
            late_return,
            high_value_return,
        )
        policy_exception_flag = bool(
            late_return
            or not receipt_present
            or item_condition == "damaged"
            or high_value_return
            or (refund_method == "store_credit" and (late_return or not receipt_present or high_value_return))
        )

        rows.append(
            {
                "return_id": f"RT{return_number:08d}",
                "sale_id": sale.sale_id,
                "transaction_id": sale.transaction_id,
                "return_date": return_date.isoformat(),
                "store_id": sale.store_id,
                "customer_id": sale.customer_id,
                "employee_id": _choose_return_employee_id(
                    rng,
                    str(sale.store_id),
                    employee_weights,
                    employees,
                ),
                "product_id": sale.product_id,
                "return_quantity": return_quantity,
                "return_amount": return_amount,
                "return_reason": return_reason,
                "return_channel": _choose_return_channel(rng, str(sale.sales_channel)),
                "refund_method": refund_method,
                "receipt_present": receipt_present,
                "item_condition": item_condition,
                "policy_exception_flag": policy_exception_flag,
            }
        )

    return pd.DataFrame(rows)


def build_datasets(
    counts: dict[str, int] | None = None,
    seed: int = RANDOM_SEED,
) -> dict[str, pd.DataFrame]:
    requested_counts = DEFAULT_COUNTS | (counts or {})
    rng = np.random.default_rng(seed)
    fake = Faker("en_CA")
    Faker.seed(seed)
    fake.seed_instance(seed)

    products = generate_products(requested_counts["products"], rng, fake)
    stores = generate_stores(requested_counts["stores"], rng)
    customers = generate_customers(requested_counts["customers"], rng)
    employees = generate_employees(requested_counts["employees"], stores, rng)
    sales = generate_sales(requested_counts["sales"], products, stores, customers, employees, rng)
    returns = generate_returns(requested_counts["returns"], sales, products, stores, employees, rng)

    return {
        "sales": sales,
        "returns": returns,
        "products": products,
        "stores": stores,
        "customers": customers,
        "employees": employees,
    }


def write_datasets(datasets: dict[str, pd.DataFrame], output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for dataset_name in CSV_ORDER:
        datasets[dataset_name].to_csv(output_path / f"{dataset_name}.csv", index=False)


def generate_all_data(
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    counts: dict[str, int] | None = None,
    seed: int = RANDOM_SEED,
) -> dict[str, pd.DataFrame]:
    datasets = build_datasets(counts=counts, seed=seed)
    write_datasets(datasets, output_dir)
    return datasets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic retail sales and returns CSV files.")
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where generated CSV files will be written.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for deterministic output.")
    parser.add_argument("--products-count", type=int, default=DEFAULT_COUNTS["products"])
    parser.add_argument("--stores-count", type=int, default=DEFAULT_COUNTS["stores"])
    parser.add_argument("--customers-count", type=int, default=DEFAULT_COUNTS["customers"])
    parser.add_argument("--employees-count", type=int, default=DEFAULT_COUNTS["employees"])
    parser.add_argument("--sales-count", type=int, default=DEFAULT_COUNTS["sales"])
    parser.add_argument("--returns-count", type=int, default=DEFAULT_COUNTS["returns"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    counts = {
        "products": args.products_count,
        "stores": args.stores_count,
        "customers": args.customers_count,
        "employees": args.employees_count,
        "sales": args.sales_count,
        "returns": args.returns_count,
    }
    generate_all_data(output_dir=args.output_dir, counts=counts, seed=args.seed)
    print(f"Generated CSV files in {Path(args.output_dir).resolve()}")


if __name__ == "__main__":
    main()
