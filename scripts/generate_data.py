from pathlib import Path
import numpy as np
import pandas as pd

np.random.seed(42)

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

N_CUSTOMERS = 30_000
N_PRODUCTS = 2_000
N_ORDERS = 250_000

START_DATE = pd.Timestamp("2024-01-01")
END_DATE = pd.Timestamp("2025-12-31")

# --------------------------------------------------
# GEOGRAPHY
# --------------------------------------------------

regions = {
    "Northeast": ["NY", "NJ", "PA", "MA"],
    "South": ["TX", "FL", "GA", "NC"],
    "Midwest": ["IL", "OH", "MI", "MN"],
    "West": ["CA", "WA", "AZ", "CO"],
}

state_to_region = {
    state: region
    for region, states in regions.items()
    for state in states
}

states = list(state_to_region.keys())

# --------------------------------------------------
# CUSTOMERS
# --------------------------------------------------

customer_ids = np.arange(1, N_CUSTOMERS + 1)

customer_states = np.random.choice(states, N_CUSTOMERS)

customer_segments = np.random.choice(
    ["Consumer", "Small Business", "Corporate"],
    N_CUSTOMERS,
    p=[0.65, 0.22, 0.13],
)

signup_dates = pd.to_datetime(
    np.random.randint(
        pd.Timestamp("2021-01-01").value // 10**9,
        END_DATE.value // 10**9,
        N_CUSTOMERS,
    ),
    unit="s",
)

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "customer_name": [f"Customer_{i:05d}" for i in customer_ids],
    "segment": customer_segments,
    "state": customer_states,
    "region": [state_to_region[s] for s in customer_states],
    "signup_date": signup_dates,
})

customers.to_csv(DATA_DIR / "customers.csv", index=False)

print("Created customers.csv")

# --------------------------------------------------
# PRODUCTS
# --------------------------------------------------

categories = {
    "Electronics": [
        "Laptops",
        "Phones",
        "Monitors",
        "Accessories",
    ],
    "Home & Office": [
        "Desks",
        "Chairs",
        "Storage",
        "Lighting",
    ],
    "Appliances": [
        "Kitchen",
        "Cleaning",
        "Climate",
        "Small Appliances",
    ],
    "Fitness": [
        "Cardio",
        "Strength",
        "Accessories",
        "Recovery",
    ],
}

category_price_ranges = {
    "Electronics": (40, 1500),
    "Home & Office": (30, 900),
    "Appliances": (25, 1200),
    "Fitness": (20, 1100),
}

product_rows = []

for product_id in range(1, N_PRODUCTS + 1):

    category = np.random.choice(list(categories.keys()))
    subcategory = np.random.choice(categories[category])

    low, high = category_price_ranges[category]

    price = round(np.random.uniform(low, high), 2)

    cost_ratio = np.random.uniform(0.48, 0.78)

    unit_cost = round(price * cost_ratio, 2)

    launch_date = START_DATE - pd.to_timedelta(
        np.random.randint(30, 1000),
        unit="D",
    )

    product_rows.append({
        "product_id": product_id,
        "product_name": f"{subcategory} Product {product_id}",
        "category": category,
        "subcategory": subcategory,
        "unit_price": price,
        "unit_cost": unit_cost,
        "launch_date": launch_date,
    })

products = pd.DataFrame(product_rows)

products.to_csv(DATA_DIR / "products.csv", index=False)

print("Created products.csv")

# --------------------------------------------------
# ORDERS
# --------------------------------------------------

order_ids = np.arange(1, N_ORDERS + 1)

date_range_days = (END_DATE - START_DATE).days + 1

order_dates = (
    START_DATE
    + pd.to_timedelta(
        np.random.randint(0, date_range_days, N_ORDERS),
        unit="D",
    )
)

orders = pd.DataFrame({
    "order_id": order_ids,
    "customer_id": np.random.choice(customer_ids, N_ORDERS),
    "order_date": order_dates,
    "sales_channel": np.random.choice(
        ["Website", "Mobile App", "Marketplace"],
        N_ORDERS,
        p=[0.50, 0.30, 0.20],
    ),
    "payment_method": np.random.choice(
        [
            "Credit Card",
            "Debit Card",
            "PayPal",
            "Digital Wallet",
        ],
        N_ORDERS,
        p=[0.42, 0.25, 0.18, 0.15],
    ),
})

orders = orders.merge(
    customers[
        [
            "customer_id",
            "state",
            "region",
            "segment",
        ]
    ],
    on="customer_id",
    how="left",
)

orders.to_csv(DATA_DIR / "orders.csv", index=False)

print("Created orders.csv")

# --------------------------------------------------
# ORDER ITEMS
# --------------------------------------------------

items_per_order = np.random.choice(
    [1, 2, 3, 4],
    N_ORDERS,
    p=[0.55, 0.28, 0.12, 0.05],
)

item_order_ids = np.repeat(
    order_ids,
    items_per_order,
)

N_ITEMS = len(item_order_ids)

item_product_ids = np.random.choice(
    products["product_id"],
    N_ITEMS,
)

order_items = pd.DataFrame({
    "order_item_id": np.arange(1, N_ITEMS + 1),
    "order_id": item_order_ids,
    "product_id": item_product_ids,
    "quantity": np.random.choice(
        [1, 2, 3, 4, 5],
        N_ITEMS,
        p=[0.62, 0.22, 0.09, 0.05, 0.02],
    ),
})

order_items = order_items.merge(
    products[
        [
            "product_id",
            "unit_price",
            "unit_cost",
            "category",
            "subcategory",
        ]
    ],
    on="product_id",
    how="left",
)

# Discounts
order_items["discount_pct"] = np.random.choice(
    [0, 0.05, 0.10, 0.15, 0.20, 0.25],
    N_ITEMS,
    p=[0.32, 0.20, 0.20, 0.13, 0.10, 0.05],
)

order_items["gross_sales"] = (
    order_items["unit_price"]
    * order_items["quantity"]
)

order_items["discount_amount"] = (
    order_items["gross_sales"]
    * order_items["discount_pct"]
)

order_items["net_sales"] = (
    order_items["gross_sales"]
    - order_items["discount_amount"]
)

order_items["cogs"] = (
    order_items["unit_cost"]
    * order_items["quantity"]
)

order_items["gross_profit"] = (
    order_items["net_sales"]
    - order_items["cogs"]
)

money_cols = [
    "gross_sales",
    "discount_amount",
    "net_sales",
    "cogs",
    "gross_profit",
]

order_items[money_cols] = (
    order_items[money_cols]
    .round(2)
)

order_items.to_csv(
    DATA_DIR / "order_items.csv",
    index=False,
)

print(
    f"Created order_items.csv "
    f"with {N_ITEMS:,} rows"
)

# --------------------------------------------------
# SHIPPING
# --------------------------------------------------

shipping_modes = np.random.choice(
    [
        "Standard",
        "Express",
        "Same Day",
    ],
    N_ORDERS,
    p=[0.66, 0.25, 0.09],
)

delivery_days = []

for mode in shipping_modes:

    if mode == "Standard":
        days = np.random.randint(3, 9)

    elif mode == "Express":
        days = np.random.randint(2, 5)

    else:
        days = np.random.randint(0, 3)

    delivery_days.append(days)

shipping_cost_map = {
    "Standard": (4, 12),
    "Express": (10, 25),
    "Same Day": (18, 40),
}

shipping_cost = [
    round(
        np.random.uniform(
            shipping_cost_map[m][0],
            shipping_cost_map[m][1],
        ),
        2,
    )
    for m in shipping_modes
]

shipping = pd.DataFrame({
    "order_id": order_ids,
    "shipping_mode": shipping_modes,
    "delivery_days": delivery_days,
    "shipping_cost": shipping_cost,
})

shipping["late_delivery"] = np.where(
    (
        (shipping["shipping_mode"] == "Standard")
        & (shipping["delivery_days"] > 6)
    )
    |
    (
        (shipping["shipping_mode"] == "Express")
        & (shipping["delivery_days"] > 3)
    )
    |
    (
        (shipping["shipping_mode"] == "Same Day")
        & (shipping["delivery_days"] > 1)
    ),
    1,
    0,
)

shipping.to_csv(
    DATA_DIR / "shipping.csv",
    index=False,
)

print("Created shipping.csv")

# --------------------------------------------------
# RETURNS
# --------------------------------------------------

return_probability = 0.08

returned_mask = (
    np.random.random(N_ITEMS)
    < return_probability
)

returned_items = order_items.loc[
    returned_mask,
    [
        "order_item_id",
        "order_id",
        "product_id",
        "net_sales",
    ],
].copy()

returned_items["return_id"] = np.arange(
    1,
    len(returned_items) + 1,
)

returned_items["return_reason"] = np.random.choice(
    [
        "Damaged",
        "Wrong Item",
        "Not as Expected",
        "Defective",
        "Changed Mind",
    ],
    len(returned_items),
    p=[0.17, 0.10, 0.30, 0.18, 0.25],
)

returned_items["refund_amount"] = (
    returned_items["net_sales"]
    * np.random.uniform(
        0.85,
        1.0,
        len(returned_items),
    )
).round(2)

returned_items[
    [
        "return_id",
        "order_item_id",
        "order_id",
        "product_id",
        "return_reason",
        "refund_amount",
    ]
].to_csv(
    DATA_DIR / "returns.csv",
    index=False,
)

print("Created returns.csv")

# --------------------------------------------------
# INVENTORY
# --------------------------------------------------

months = pd.date_range(
    START_DATE,
    END_DATE,
    freq="MS",
)

inventory_rows = []

for month in months:

    for product_id in products["product_id"]:

        opening_inventory = np.random.randint(
            40,
            800,
        )

        units_received = np.random.randint(
            0,
            400,
        )

        units_sold = np.random.randint(
            10,
            min(
                opening_inventory + units_received,
                350,
            ) + 1,
        )

        closing_inventory = max(
            opening_inventory
            + units_received
            - units_sold,
            0,
        )

        inventory_rows.append({
            "month": month,
            "product_id": product_id,
            "opening_inventory": opening_inventory,
            "units_received": units_received,
            "units_sold": units_sold,
            "closing_inventory": closing_inventory,
        })

inventory = pd.DataFrame(
    inventory_rows
)

inventory.to_csv(
    DATA_DIR / "inventory.csv",
    index=False,
)

print("Created inventory.csv")

# --------------------------------------------------
# MARKETING SPEND
# --------------------------------------------------

marketing_channels = [
    "Paid Search",
    "Social Media",
    "Email",
    "Affiliate",
]

marketing_rows = []

for month in months:

    for region in regions:

        for channel in marketing_channels:

            spend = np.random.uniform(
                8_000,
                80_000,
            )

            impressions = np.random.randint(
                150_000,
                2_000_000,
            )

            clicks = int(
                impressions
                * np.random.uniform(
                    0.015,
                    0.06,
                )
            )

            conversions = int(
                clicks
                * np.random.uniform(
                    0.015,
                    0.08,
                )
            )

            marketing_rows.append({
                "month": month,
                "region": region,
                "channel": channel,
                "spend": round(spend, 2),
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
            })

marketing = pd.DataFrame(
    marketing_rows
)

marketing.to_csv(
    DATA_DIR / "marketing_spend.csv",
    index=False,
)

print("Created marketing_spend.csv")

# --------------------------------------------------
# TARGETS
# --------------------------------------------------

target_rows = []

for month in months:

    for region in regions:

        target_rows.append({
            "month": month,
            "region": region,
            "revenue_target": round(
                np.random.uniform(
                    4_000_000,
                    8_000_000,
                ),
                2,
            ),
            "profit_target": round(
                np.random.uniform(
                    800_000,
                    2_000_000,
                ),
                2,
            ),
        })

targets = pd.DataFrame(
    target_rows
)

targets.to_csv(
    DATA_DIR / "targets.csv",
    index=False,
)

print("Created targets.csv")

# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\nDATA GENERATION COMPLETE")
print("-------------------------")

for file in DATA_DIR.glob("*.csv"):

    df = pd.read_csv(file)

    print(
        f"{file.name:<25}"
        f"{len(df):>12,} rows"
    )