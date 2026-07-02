from datetime import date
from pathlib import Path


RANDOM_SEED = 42

DEFAULT_OUTPUT_DIR = Path("data/sample")

DEFAULT_COUNTS = {
    "products": 500,
    "stores": 20,
    "customers": 10_000,
    "employees": 150,
    "sales": 50_000,
    "returns": 6_000,
}

SALES_START_DATE = date(2024, 1, 1)
SALES_END_DATE = date(2025, 12, 31)

CUSTOMER_SIGNUP_START_DATE = date(2018, 1, 1)
STORE_OPEN_START_DATE = date(2010, 1, 1)
EMPLOYEE_HIRE_START_DATE = date(2018, 1, 1)

ONTARIO_LOCATIONS = [
    ("Toronto", "ON", "Greater Toronto Area"),
    ("Mississauga", "ON", "Greater Toronto Area"),
    ("Brampton", "ON", "Greater Toronto Area"),
    ("Markham", "ON", "Greater Toronto Area"),
    ("Vaughan", "ON", "Greater Toronto Area"),
    ("Oakville", "ON", "Greater Toronto Area"),
    ("Hamilton", "ON", "Golden Horseshoe"),
    ("Burlington", "ON", "Golden Horseshoe"),
    ("St. Catharines", "ON", "Golden Horseshoe"),
    ("Niagara Falls", "ON", "Golden Horseshoe"),
    ("London", "ON", "Southwestern Ontario"),
    ("Windsor", "ON", "Southwestern Ontario"),
    ("Kitchener", "ON", "Southwestern Ontario"),
    ("Waterloo", "ON", "Southwestern Ontario"),
    ("Guelph", "ON", "Southwestern Ontario"),
    ("Ottawa", "ON", "Eastern Ontario"),
    ("Kingston", "ON", "Eastern Ontario"),
    ("Peterborough", "ON", "Central Ontario"),
    ("Barrie", "ON", "Central Ontario"),
    ("Sudbury", "ON", "Northern Ontario"),
    ("Thunder Bay", "ON", "Northern Ontario"),
]

PRODUCT_CATALOG = {
    "apparel": ["tops", "bottoms", "outerwear", "footwear", "accessories"],
    "electronics": ["mobile_accessories", "audio", "computers", "smart_home", "gaming"],
    "home": ["kitchen", "bedding", "decor", "storage", "cleaning"],
    "beauty": ["skincare", "haircare", "fragrance", "makeup", "personal_care"],
    "grocery": ["pantry", "snacks", "beverages", "household", "pet"],
    "sporting_goods": ["fitness", "outdoor", "team_sports", "cycling", "winter_sports"],
}

BRANDS = [
    "Maple & Main",
    "Northline",
    "Lakeview",
    "Harbour Goods",
    "TrueLeaf",
    "Urban Trail",
    "Cedar Works",
    "BrightNest",
    "Fieldstone",
    "Summit House",
    "Evervale",
    "Canopy Co.",
]

STORE_TYPES = ["flagship", "mall", "outlet", "neighbourhood", "warehouse"]

LOYALTY_TIERS = ["none", "bronze", "silver", "gold", "platinum"]

EMPLOYEE_ROLES = [
    "sales_associate",
    "cashier",
    "customer_service",
    "returns_specialist",
    "stock_associate",
    "supervisor",
    "manager",
]

PAYMENT_METHODS = ["credit_card", "debit_card", "cash", "gift_card", "store_credit"]
SALES_CHANNELS = ["in_store", "online", "curbside_pickup"]
RETURN_CHANNELS = ["in_store", "mail", "curbside"]

RETURN_REASONS = [
    "changed_mind",
    "wrong_size",
    "defective",
    "damaged",
    "not_as_described",
    "duplicate_purchase",
    "late_delivery",
    "other",
]

ITEM_CONDITIONS = [
    "unopened",
    "opened",
    "damaged",
    "defective",
    "missing_packaging",
]
