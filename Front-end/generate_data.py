"""
Data generation script - creates realistic CSV/JSON data for all stores.
Run once: python generate_data.py
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

STORES = ["Store A - Downtown", "Store B - Mall", "Store C - Suburb", "Store D - Airport"]
PRODUCTS = {
    "Apples":   {"category": "Fresh Produce", "shelf_days": 7,  "base_price": 2.50},
    "Bananas":  {"category": "Fresh Produce", "shelf_days": 5,  "base_price": 1.20},
    "Lettuce":  {"category": "Fresh Produce", "shelf_days": 4,  "base_price": 1.80},
    "Tomatoes": {"category": "Fresh Produce", "shelf_days": 5,  "base_price": 2.20},
    "Milk":     {"category": "Dairy",         "shelf_days": 7,  "base_price": 1.50},
    "Cheese":   {"category": "Dairy",         "shelf_days": 14, "base_price": 5.00},
    "Yogurt":   {"category": "Dairy",         "shelf_days": 10, "base_price": 2.00},
    "Chicken":  {"category": "Meat",          "shelf_days": 3,  "base_price": 7.50},
    "Beef":     {"category": "Meat",          "shelf_days": 4,  "base_price": 10.0},
    "Bread":    {"category": "Bakery",        "shelf_days": 5,  "base_price": 2.80},
    "Oranges":  {"category": "Fresh Produce", "shelf_days": 10, "base_price": 2.00},
    "Carrots":  {"category": "Fresh Produce", "shelf_days": 14, "base_price": 1.50},
    "Salmon":   {"category": "Meat",          "shelf_days": 2,  "base_price": 12.0},
    "Butter":   {"category": "Dairy",         "shelf_days": 30, "base_price": 3.50},
    "Muffins":  {"category": "Bakery",        "shelf_days": 3,  "base_price": 3.00},
}

WASTE_REASONS = ["Expired", "Damaged", "Overstock", "Quality Issues", "Customer Return", "Staff Error", "Other"]
SUPPLIERS = ["FreshFarm Co.", "DairyBest Ltd.", "MeatMaster Inc.", "BakerySupply Co.", "GreenLeaf Farms"]

rng = np.random.default_rng(42)
os.makedirs("data", exist_ok=True)

# ── Sales Data (90 days) ──────────────────────────────────────────────────────
sales_rows = []
today = datetime.now().date()
base_demands = {
    "Store A - Downtown": 1.3,
    "Store B - Mall":     1.1,
    "Store C - Suburb":   0.9,
    "Store D - Airport":  0.7,
}

for store in STORES:
    for day_offset in range(90, 0, -1):
        date = today - timedelta(days=day_offset)
        dow = date.weekday()  # 0=Mon
        weekend = 1.25 if dow >= 5 else 1.0
        for product, meta in PRODUCTS.items():
            base = rng.integers(40, 140)
            seasonal = 1 + 0.15 * np.sin(2 * np.pi * day_offset / 30)
            trend = 1 + 0.002 * (90 - day_offset)  # slight upward trend
            actual = max(1, int(base * base_demands[store] * seasonal * weekend * trend
                                * rng.uniform(0.88, 1.12)))
            noise = rng.uniform(0.93, 1.07)
            predicted = max(1, int(actual * noise))
            sales_rows.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Store": store,
                "Product": product,
                "Category": meta["category"],
                "Actual_Sales": actual,
                "Predicted_Sales": predicted,
                "Unit_Price": round(meta["base_price"] * rng.uniform(0.9, 1.1), 2),
            })

sales_df = pd.DataFrame(sales_rows)
sales_df.to_csv("data/sales_data.csv", index=False)
print(f"Sales data: {len(sales_df)} rows")

# ── Waste Data (90 days) ──────────────────────────────────────────────────────
waste_rows = []
perishable = ["Bananas", "Lettuce", "Tomatoes", "Milk", "Chicken", "Salmon", "Bread", "Muffins"]
semi_perishable = ["Apples", "Oranges", "Yogurt", "Beef", "Cheese"]

for store in STORES:
    for day_offset in range(90, 0, -1):
        date = today - timedelta(days=day_offset)
        n_waste_events = rng.integers(2, 7)
        products_today = rng.choice(list(PRODUCTS.keys()), size=n_waste_events, replace=False)
        for product in products_today:
            if product in perishable:
                qty = round(float(rng.uniform(1.5, 12.0)), 2)
            elif product in semi_perishable:
                qty = round(float(rng.uniform(0.5, 6.0)), 2)
            else:
                qty = round(float(rng.uniform(0.2, 3.0)), 2)

            reason = rng.choice(WASTE_REASONS, p=[0.35, 0.20, 0.18, 0.12, 0.07, 0.05, 0.03])
            unit = "kg" if PRODUCTS[product]["category"] in ("Fresh Produce", "Meat", "Dairy") else "pcs"
            value = round(float(qty * PRODUCTS[product]["base_price"] * rng.uniform(0.8, 1.2)), 2)
            waste_rows.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Store": store,
                "Product": product,
                "Category": PRODUCTS[product]["category"],
                "Quantity": qty,
                "Unit": unit,
                "Reason": reason,
                "Value_Lost": value,
                "Notes": "",
            })

waste_df = pd.DataFrame(waste_rows)
waste_df.to_csv("data/waste_data.csv", index=False)
print(f"Waste data: {len(waste_df)} rows")

# ── Product Master ────────────────────────────────────────────────────────────
product_rows = []
for store in STORES:
    multiplier = base_demands[store]
    for product, meta in PRODUCTS.items():
        stock = int(rng.integers(15, 120) * multiplier)
        reorder = int(rng.integers(10, 30))
        price = round(meta["base_price"] * rng.uniform(0.9, 1.3), 2)
        supplier = rng.choice(SUPPLIERS)
        # Compute expiry: random between today+1 and today+shelf_days
        days_to_exp = int(rng.integers(1, meta["shelf_days"] + 1))
        expiry = (today + timedelta(days=days_to_exp)).strftime("%Y-%m-%d")
        risk_map = {"Fresh Produce": rng.integers(55, 90),
                    "Dairy": rng.integers(45, 80),
                    "Meat": rng.integers(60, 95),
                    "Bakery": rng.integers(40, 75)}
        waste_risk = int(risk_map.get(meta["category"], rng.integers(20, 60)))
        product_rows.append({
            "Store": store,
            "Product Name": product,
            "Category": meta["category"],
            "Current Stock": stock,
            "Reorder Level": reorder,
            "Unit Price": price,
            "Supplier": supplier,
            "Status": "Active",
            "Expiry Date": expiry,
            "Waste Risk %": waste_risk,
        })

products_df = pd.DataFrame(product_rows)
products_df.to_csv("data/product_master.csv", index=False)
print(f"Product master: {len(products_df)} rows")

# ── Event Data ────────────────────────────────────────────────────────────────
events = []
event_templates = [
    ("Summer Festival", "City Park", "High", 1.35),
    ("Marathon Run", "Downtown Street", "Medium", 1.20),
    ("School Reopening", "Local Schools", "Medium", 1.15),
    ("Concert Night", "Stadium", "High", 1.30),
    ("Public Holiday", "Citywide", "High", 1.40),
    ("Food Fair", "Exhibition Hall", "Medium", 1.25),
    ("Sports Finals", "Sports Arena", "High", 1.35),
    ("Weekly Market", "Town Square", "Low", 1.10),
]
eid = 1
for store in STORES:
    for i, (name, loc, impact, _) in enumerate(event_templates):
        offset = rng.integers(-30, 45)
        edate = (today + timedelta(days=int(offset))).strftime("%Y-%m-%d")
        events.append({
            "id": eid, "name": name, "location": loc, "date": edate,
            "impact": impact, "description": f"{name} near {store}.",
            "store": store, "created_at": str(datetime.now())
        })
        eid += 1

with open("data/event_data.json", "w") as f:
    json.dump(events, f, indent=2)
print(f"Events: {len(events)}")
print("All data files generated successfully.")
