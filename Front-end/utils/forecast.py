"""
forecast.py — Fixed & enhanced ForecastEngine
Fixes:
 - All forecast periods (Today/Tomorrow/Next 3 Days/Next Week/Monthly/Yearly) work correctly
 - Deterministic predictions (no random on each rerun)
 - Proper period-aggregated analytics for charts
 - Accurate waste risk calculation
 - Robust file I/O with full error handling
 - Duplicate product prevention
 - save_product_updates correctly preserves other stores
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import hashlib

STORES = ["Store A - Downtown", "Store B - Mall", "Store C - Suburb", "Store D - Airport"]
PRODUCTS_META = {
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
VALID_CATEGORIES = ["Fresh Produce", "Dairy", "Meat", "Bakery", "Pantry"]
DATA_DIR = "data"


def _seed(store: str, product: str, date_str: str) -> int:
    """Deterministic seed so forecasts don't flicker on every rerun."""
    key = f"{store}:{product}:{date_str}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**31)


class ForecastEngine:
    def __init__(self):
        self.products = list(PRODUCTS_META.keys())
        self._ensure_data_files()

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _ensure_data_files(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(f"{DATA_DIR}/sales_data.csv"):
            self._create_sample_sales_data()
        if not os.path.exists(f"{DATA_DIR}/product_master.csv"):
            self._create_product_master()
        if not os.path.exists(f"{DATA_DIR}/waste_data.csv"):
            self._create_sample_waste_data()

    def _create_sample_sales_data(self):
        today = datetime.now().date()
        rows = []
        for store in STORES:
            mult = {"Store A - Downtown": 1.3, "Store B - Mall": 1.1,
                    "Store C - Suburb": 0.9, "Store D - Airport": 0.7}.get(store, 1.0)
            for offset in range(90, 0, -1):
                date = today - timedelta(days=offset)
                dow = date.weekday()
                weekend = 1.25 if dow >= 5 else 1.0
                for product, meta in PRODUCTS_META.items():
                    rng = np.random.default_rng(_seed(store, product, str(date)))
                    base = rng.integers(40, 140)
                    actual = max(1, int(base * mult * weekend * rng.uniform(0.88, 1.12)))
                    predicted = max(1, int(actual * rng.uniform(0.93, 1.07)))
                    rows.append({"Date": str(date), "Store": store, "Product": product,
                                 "Category": meta["category"], "Actual_Sales": actual,
                                 "Predicted_Sales": predicted,
                                 "Unit_Price": round(meta["base_price"] * 1.0, 2)})
        pd.DataFrame(rows).to_csv(f"{DATA_DIR}/sales_data.csv", index=False)

    def _create_product_master(self):
        rows = []
        today = datetime.now().date()
        for store in STORES:
            for product, meta in PRODUCTS_META.items():
                rng = np.random.default_rng(_seed(store, product, "master"))
                stock = int(rng.integers(15, 120))
                reorder = int(rng.integers(10, 30))
                price = round(meta["base_price"] * float(rng.uniform(0.9, 1.3)), 2)
                expiry = (today + timedelta(days=int(rng.integers(1, meta["shelf_days"] + 1)))).strftime("%Y-%m-%d")
                supplier = rng.choice(["FreshFarm Co.", "DairyBest Ltd.", "MeatMaster Inc.",
                                       "BakerySupply Co.", "GreenLeaf Farms"])
                risk_ranges = {"Fresh Produce": (55, 90), "Dairy": (45, 80),
                               "Meat": (60, 95), "Bakery": (40, 75)}
                lo, hi = risk_ranges.get(meta["category"], (20, 60))
                rows.append({"Store": store, "Product Name": product, "Category": meta["category"],
                              "Current Stock": stock, "Reorder Level": reorder, "Unit Price": price,
                              "Supplier": str(supplier), "Status": "Active",
                              "Expiry Date": expiry, "Waste Risk %": int(rng.integers(lo, hi))})
        pd.DataFrame(rows).to_csv(f"{DATA_DIR}/product_master.csv", index=False)

    def _create_sample_waste_data(self):
        today = datetime.now().date()
        rows = []
        reasons = ["Expired", "Damaged", "Overstock", "Quality Issues", "Customer Return", "Staff Error", "Other"]
        for store in STORES:
            for offset in range(90, 0, -1):
                date = today - timedelta(days=offset)
                rng = np.random.default_rng(_seed(store, "waste", str(date)))
                for product, meta in list(PRODUCTS_META.items())[:8]:
                    if rng.random() < 0.55:
                        qty = round(float(rng.uniform(0.5, 8.0)), 2)
                        reason = reasons[int(rng.integers(0, len(reasons)))]
                        unit = "kg" if meta["category"] in ("Fresh Produce", "Meat", "Dairy") else "pcs"
                        value = round(qty * meta["base_price"], 2)
                        rows.append({"Date": str(date), "Store": store, "Product": product,
                                     "Category": meta["category"], "Quantity": qty, "Unit": unit,
                                     "Reason": reason, "Value_Lost": value, "Notes": ""})
        pd.DataFrame(rows).to_csv(f"{DATA_DIR}/waste_data.csv", index=False)

    def _load_sales(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(f"{DATA_DIR}/sales_data.csv")
            df["Date"] = pd.to_datetime(df["Date"])
            return df
        except Exception:
            return pd.DataFrame()

    def _load_waste(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(f"{DATA_DIR}/waste_data.csv")
            df["Date"] = pd.to_datetime(df["Date"])
            return df
        except Exception:
            return pd.DataFrame()

    def _load_products(self) -> pd.DataFrame:
        try:
            return pd.read_csv(f"{DATA_DIR}/product_master.csv")
        except Exception:
            return pd.DataFrame()

    # ──────────────────────────────────────────────────────────────────────────
    # Product Management
    # ──────────────────────────────────────────────────────────────────────────
    def get_product_list(self, store: str) -> pd.DataFrame:
        products_df = self._load_products()
        if products_df.empty:
            return pd.DataFrame()
        store_products = products_df[products_df["Store"] == store].copy()
        # Refresh waste risk
        waste_risks = self._compute_waste_risks(store)
        for idx, row in store_products.iterrows():
            name = row["Product Name"]
            store_products.at[idx, "Waste Risk %"] = waste_risks.get(name, row.get("Waste Risk %", 0))
        return store_products.reset_index(drop=True)

    def _compute_waste_risks(self, store: str) -> dict:
        """Stable per-product waste risk based on waste vs sales ratio."""
        waste_df = self._load_waste()
        sales_df = self._load_sales()
        risks = {}
        if waste_df.empty or sales_df.empty:
            return risks
        sw = waste_df[waste_df["Store"] == store] if "Store" in waste_df.columns else waste_df
        ss = sales_df[sales_df["Store"] == store] if "Store" in sales_df.columns else sales_df
        cutoff = datetime.now() - timedelta(days=30)
        sw = sw[sw["Date"] >= cutoff]
        ss = ss[ss["Date"] >= cutoff]
        for product in sw["Product"].unique() if "Product" in sw.columns else []:
            pw = sw[sw["Product"] == product]["Quantity"].sum()
            ps = ss[ss["Product"] == product]["Actual_Sales"].sum() if "Product" in ss.columns else 0
            if ps > 0:
                risks[product] = min(100, max(0, int(pw / ps * 100)))
            else:
                risks[product] = 50
        return risks

    def apply_product_filters(self, df: pd.DataFrame, category_filter: str,
                               risk_filter: str, stock_filter: str) -> pd.DataFrame:
        f = df.copy()
        if category_filter != "All":
            f = f[f["Category"] == category_filter]
        if risk_filter == "High Risk (>70%)":
            f = f[f["Waste Risk %"] > 70]
        elif risk_filter == "Medium Risk (30-70%)":
            f = f[(f["Waste Risk %"] >= 30) & (f["Waste Risk %"] <= 70)]
        elif risk_filter == "Low Risk (<30%)":
            f = f[f["Waste Risk %"] < 30]
        if stock_filter == "Low Stock":
            f = f[f["Current Stock"] <= f["Reorder Level"]]
        elif stock_filter == "Out of Stock":
            f = f[f["Current Stock"] == 0]
        elif stock_filter == "In Stock":
            f = f[f["Current Stock"] > f["Reorder Level"]]
        return f

    def validate_new_product(self, store: str, name: str, category: str,
                              stock: float, reorder: float, price: float,
                              supplier: str, expiry_date: str) -> list:
        """Returns list of validation error strings. Empty = valid."""
        errors = []
        if not name or not name.strip():
            errors.append("Product name is required.")
        elif len(name.strip()) < 2:
            errors.append("Product name must be at least 2 characters.")
        if category not in VALID_CATEGORIES:
            errors.append(f"Category must be one of: {', '.join(VALID_CATEGORIES)}.")
        if stock < 0:
            errors.append("Stock quantity cannot be negative.")
        if reorder < 0:
            errors.append("Reorder level cannot be negative.")
        if price <= 0:
            errors.append("Unit price must be greater than 0.")
        if not supplier or not supplier.strip():
            errors.append("Supplier name is required.")
        # Expiry date validation
        try:
            exp = datetime.strptime(expiry_date, "%Y-%m-%d").date()
            if exp <= datetime.now().date():
                errors.append("Expiry date must be in the future.")
        except ValueError:
            errors.append("Invalid expiry date format.")
        # Duplicate check
        products_df = self._load_products()
        if not products_df.empty:
            dupes = products_df[
                (products_df["Store"] == store) &
                (products_df["Product Name"].str.lower() == name.strip().lower())
            ]
            if not dupes.empty:
                errors.append(f"Product '{name.strip()}' already exists in {store}.")
        return errors

    def add_new_product(self, store, name, category, stock, reorder, price,
                        supplier, expiry_date, status="Active"):
        try:
            products_df = self._load_products()
            new_row = pd.DataFrame([{
                "Store": store, "Product Name": name.strip(), "Category": category,
                "Current Stock": int(stock), "Reorder Level": int(reorder),
                "Unit Price": round(float(price), 2), "Supplier": supplier.strip(),
                "Status": status, "Expiry Date": expiry_date, "Waste Risk %": 0
            }])
            products_df = pd.concat([products_df, new_row], ignore_index=True)
            products_df.to_csv(f"{DATA_DIR}/product_master.csv", index=False)
            return True
        except Exception as e:
            print(f"add_new_product error: {e}")
            return False

    def save_product_updates(self, updated_df: pd.DataFrame, store: str) -> bool:
        try:
            all_products = self._load_products()
            # Drop old rows for this store
            other_stores = all_products[all_products["Store"] != store]
            updated_df = updated_df.copy()
            updated_df["Store"] = store
            combined = pd.concat([other_stores, updated_df], ignore_index=True)
            combined.to_csv(f"{DATA_DIR}/product_master.csv", index=False)
            return True
        except Exception as e:
            print(f"save_product_updates error: {e}")
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Forecast
    # ──────────────────────────────────────────────────────────────────────────
    def get_enhanced_forecast(self, store: str, period: str) -> pd.DataFrame:
        """
        period options: Today | Tomorrow | Next 3 Days | Next Week |
                        Daily | Weekly | Monthly | Yearly
        Returns per-product aggregated forecast for the requested window.
        """
        today = datetime.now().date()
        period_map = {
            "Today":       (today, today),
            "Tomorrow":    (today + timedelta(1), today + timedelta(1)),
            "Next 3 Days": (today + timedelta(1), today + timedelta(3)),
            "Next Week":   (today + timedelta(1), today + timedelta(7)),
            "Daily":       (today, today),
            "Weekly":      (today, today + timedelta(6)),
            "Monthly":     (today, today + timedelta(29)),
            "Yearly":      (today, today + timedelta(364)),
        }
        start, end = period_map.get(period, (today, today))
        days = max(1, (end - start).days + 1)

        sales_df = self._load_sales()
        products_df = self.get_product_list(store)

        rows = []
        for _, prow in products_df.iterrows():
            product = prow["Product Name"]
            # Historical avg daily from last 30 days
            if not sales_df.empty:
                ps = sales_df[(sales_df["Store"] == store) & (sales_df["Product"] == product)]
                cutoff = datetime.now() - timedelta(days=30)
                ps = ps[ps["Date"] >= cutoff]
                if not ps.empty:
                    avg_daily = ps["Actual_Sales"].mean()
                else:
                    avg_daily = 60.0
            else:
                avg_daily = 60.0

            # Deterministic jitter per (store, product, period)
            rng = np.random.default_rng(_seed(store, product, f"{period}:{today}"))
            trend_factor = float(rng.uniform(0.95, 1.08))
            predicted_total = max(1, int(avg_daily * days * trend_factor))

            waste_risk = int(prow.get("Waste Risk %", 30))
            confidence = max(60, min(97, 90 - waste_risk // 5 + int(rng.integers(0, 6))))

            if waste_risk > 70:
                action = "⚠️ Reduce order / discount soon"
            elif waste_risk > 40:
                action = "⚡ Monitor closely"
            else:
                action = "✅ Safe to order"

            rows.append({
                "Product Name": product,
                "Category": prow.get("Category", ""),
                "Predicted Qty": predicted_total,
                "Manual Override": 0,
                "Final Qty": predicted_total,
                "Waste Risk %": waste_risk,
                "Confidence": confidence,
                "Current Stock": int(prow.get("Current Stock", 0)),
                "Suggested Action": action,
            })

        return pd.DataFrame(rows)

    def save_forecast(self, forecast_df: pd.DataFrame, store: str, period: str) -> bool:
        try:
            os.makedirs(f"{DATA_DIR}/forecasts", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_store = store.replace(" ", "_").replace("-", "")
            safe_period = period.replace(" ", "_")
            path = f"{DATA_DIR}/forecasts/forecast_{safe_store}_{safe_period}_{ts}.csv"
            forecast_df.to_csv(path, index=False)
            return True
        except Exception as e:
            print(f"save_forecast error: {e}")
            return False

    def get_forecast_accuracy(self, store: str) -> dict:
        try:
            sales_df = self._load_sales()
            ss = sales_df[sales_df["Store"] == store]
            if ss.empty:
                return {"weekly": 88.0, "monthly": 85.0, "trend": "Stable", "trend_delta": "0.0%"}

            def accuracy(data):
                if data.empty or "Predicted_Sales" not in data.columns:
                    return 85.0
                a = data["Actual_Sales"].sum()
                p = data["Predicted_Sales"].sum()
                return max(0.0, min(100.0, 100 - abs(a - p) / max(a, 1) * 100))

            today = datetime.now()
            weekly = accuracy(ss[ss["Date"] >= today - timedelta(days=7)])
            monthly = accuracy(ss[ss["Date"] >= today - timedelta(days=30)])
            trend = "Improving" if weekly > monthly else ("Declining" if weekly < monthly else "Stable")
            return {"weekly": round(weekly, 1), "monthly": round(monthly, 1),
                    "trend": trend, "trend_delta": f"{abs(weekly - monthly):.1f}%"}
        except Exception as e:
            print(f"get_forecast_accuracy error: {e}")
            return {"weekly": 88.0, "monthly": 85.0, "trend": "Stable", "trend_delta": "0.0%"}

    def generate_forecast_pdf(self, forecast_df: pd.DataFrame, store: str, period: str) -> bytes:
        html = f"""<html><head><title>Forecast — {store}</title>
        <style>body{{font-family:Arial;margin:30px}}table{{border-collapse:collapse;width:100%}}
        th,td{{border:1px solid #ccc;padding:8px;text-align:left}}th{{background:#4CAF50;color:#fff}}
        tr:nth-child(even){{background:#f9f9f9}}</style></head><body>
        <h1>📊 Smart Forecasting Report</h1>
        <p><b>Store:</b> {store} &nbsp;|&nbsp; <b>Period:</b> {period} &nbsp;|&nbsp;
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <table><tr><th>Product</th><th>Category</th><th>AI Prediction</th>
        <th>Final Forecast</th><th>Waste Risk</th><th>Confidence</th><th>Action</th></tr>"""
        for _, row in forecast_df.iterrows():
            html += f"""<tr><td>{row['Product Name']}</td><td>{row.get('Category','')}</td>
            <td>{row['Predicted Qty']}</td><td>{row['Final Qty']}</td>
            <td>{row['Waste Risk %']}%</td><td>{row['Confidence']}%</td>
            <td>{row['Suggested Action']}</td></tr>"""
        html += "</table></body></html>"
        return html.encode("utf-8")

    # ──────────────────────────────────────────────────────────────────────────
    # Analytics
    # ──────────────────────────────────────────────────────────────────────────
    def get_sales_analytics(self, store: str, period: str) -> pd.DataFrame:
        try:
            df = self._load_sales()
            if df.empty:
                return pd.DataFrame()
            ss = df[df["Store"] == store].copy()
            if ss.empty:
                return pd.DataFrame()

            if period == "Daily":
                g = ss.groupby("Date").agg(Actual_Sales=("Actual_Sales", "sum"),
                                            Predicted_Sales=("Predicted_Sales", "sum")).reset_index()
                g["Date"] = g["Date"].dt.strftime("%Y-%m-%d")
                return g
            elif period == "Weekly":
                ss["Week"] = ss["Date"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
                g = ss.groupby("Week").agg(Actual_Sales=("Actual_Sales", "sum"),
                                            Predicted_Sales=("Predicted_Sales", "sum")).reset_index()
                return g
            elif period == "Monthly":
                ss["Month"] = ss["Date"].dt.to_period("M").dt.strftime("%Y-%m")
                g = ss.groupby("Month").agg(Actual_Sales=("Actual_Sales", "sum"),
                                             Predicted_Sales=("Predicted_Sales", "sum")).reset_index()
                return g
            elif period == "Yearly":
                ss["Year"] = ss["Date"].dt.year.astype(str)
                g = ss.groupby("Year").agg(Actual_Sales=("Actual_Sales", "sum"),
                                            Predicted_Sales=("Predicted_Sales", "sum")).reset_index()
                return g
            else:
                g = ss.groupby("Date").agg(Actual_Sales=("Actual_Sales", "sum"),
                                            Predicted_Sales=("Predicted_Sales", "sum")).reset_index()
                g["Date"] = g["Date"].dt.strftime("%Y-%m-%d")
                return g
        except Exception as e:
            print(f"get_sales_analytics error: {e}")
            return pd.DataFrame()

    def get_sales_by_category(self, store: str, period: str) -> pd.DataFrame:
        try:
            df = self._load_sales()
            if df.empty or "Category" not in df.columns:
                return pd.DataFrame()
            ss = df[df["Store"] == store].copy()
            if ss.empty:
                return pd.DataFrame()
            g = ss.groupby("Category")["Actual_Sales"].sum().reset_index()
            g.columns = ["Category", "Total_Sales"]
            return g.sort_values("Total_Sales", ascending=False)
        except Exception as e:
            print(f"get_sales_by_category error: {e}")
            return pd.DataFrame()

    def get_top_products(self, store: str, n: int = 10) -> pd.DataFrame:
        try:
            df = self._load_sales()
            ss = df[df["Store"] == store] if not df.empty else pd.DataFrame()
            if ss.empty:
                return pd.DataFrame()
            g = ss.groupby("Product")["Actual_Sales"].sum().reset_index()
            g.columns = ["Product", "Total_Sales"]
            return g.sort_values("Total_Sales", ascending=False).head(n)
        except Exception as e:
            print(f"get_top_products error: {e}")
            return pd.DataFrame()

    def get_waste_analytics(self, store: str, period: str) -> pd.DataFrame:
        try:
            df = self._load_waste()
            if df.empty:
                return pd.DataFrame()
            sw = df[df["Store"] == store].copy() if "Store" in df.columns else df.copy()
            if sw.empty:
                return pd.DataFrame()

            if period == "Daily":
                g = sw.groupby("Date").agg(Quantity=("Quantity", "sum"),
                                            Value_Lost=("Value_Lost", "sum") if "Value_Lost" in sw.columns else ("Quantity", "sum")).reset_index()
                g["Date"] = g["Date"].dt.strftime("%Y-%m-%d")
                return g
            elif period == "Weekly":
                sw["Week"] = sw["Date"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
                g = sw.groupby("Week")["Quantity"].sum().reset_index()
                return g
            elif period == "Monthly":
                sw["Month"] = sw["Date"].dt.to_period("M").dt.strftime("%Y-%m")
                g = sw.groupby("Month")["Quantity"].sum().reset_index()
                return g
            elif period == "Yearly":
                sw["Year"] = sw["Date"].dt.year.astype(str)
                g = sw.groupby("Year")["Quantity"].sum().reset_index()
                return g
            else:
                g = sw.groupby("Date")["Quantity"].sum().reset_index()
                g["Date"] = g["Date"].dt.strftime("%Y-%m-%d")
                return g
        except Exception as e:
            print(f"get_waste_analytics error: {e}")
            return pd.DataFrame()

    def get_waste_by_category(self, store: str) -> pd.DataFrame:
        try:
            df = self._load_waste()
            sw = df[df["Store"] == store] if not df.empty and "Store" in df.columns else df
            if sw.empty or "Category" not in sw.columns:
                return pd.DataFrame()
            g = sw.groupby("Category")["Quantity"].sum().reset_index()
            g.columns = ["Category", "Total_Waste"]
            return g.sort_values("Total_Waste", ascending=False)
        except Exception as e:
            print(f"get_waste_by_category error: {e}")
            return pd.DataFrame()

    def get_waste_by_reason(self, store: str) -> pd.DataFrame:
        try:
            df = self._load_waste()
            sw = df[df["Store"] == store] if not df.empty and "Store" in df.columns else df
            if sw.empty or "Reason" not in sw.columns:
                return pd.DataFrame()
            g = sw.groupby("Reason")["Quantity"].sum().reset_index()
            g.columns = ["Reason", "Total_Waste"]
            return g.sort_values("Total_Waste", ascending=False)
        except Exception as e:
            print(f"get_waste_by_reason error: {e}")
            return pd.DataFrame()

    def get_waste_by_product(self, store: str) -> pd.DataFrame:
        try:
            df = self._load_waste()
            sw = df[df["Store"] == store] if not df.empty and "Store" in df.columns else df
            if sw.empty:
                return pd.DataFrame()
            g = sw.groupby("Product")["Quantity"].sum().reset_index()
            g.columns = ["Product", "Total_Waste"]
            return g.sort_values("Total_Waste", ascending=False).head(15)
        except Exception as e:
            print(f"get_waste_by_product error: {e}")
            return pd.DataFrame()

    def get_store_waste_comparison(self) -> pd.DataFrame:
        try:
            df = self._load_waste()
            if df.empty or "Store" not in df.columns:
                return pd.DataFrame()
            g = df.groupby("Store")["Quantity"].sum().reset_index()
            g.columns = ["Store", "Total_Waste"]
            return g.sort_values("Total_Waste", ascending=False)
        except Exception as e:
            print(f"get_store_waste_comparison error: {e}")
            return pd.DataFrame()

    def get_combined_analytics(self, store: str, period: str) -> pd.DataFrame:
        sales = self.get_sales_analytics(store, period)
        waste = self.get_waste_analytics(store, period)
        if sales.empty and waste.empty:
            return pd.DataFrame()
        key_map = {"Daily": "Date", "Weekly": "Week", "Monthly": "Month", "Yearly": "Year"}
        key = key_map.get(period, "Date")
        if not sales.empty and key in sales.columns:
            sales = sales.rename(columns={"Actual_Sales": "Sales"})
        if not waste.empty and key in waste.columns:
            waste = waste.rename(columns={"Quantity": "Waste"})
        if sales.empty:
            return waste
        if waste.empty:
            return sales
        merged = pd.merge(sales[[key, "Sales"]], waste[[key, "Waste"]], on=key, how="outer").fillna(0)
        return merged

    def generate_sales_report(self, store: str, period: str, report_type: str) -> pd.DataFrame:
        try:
            if report_type == "Sales Report":
                return self.get_sales_analytics(store, period)
            elif report_type == "Waste Report":
                return self.get_waste_analytics(store, period)
            else:
                return self.get_combined_analytics(store, period)
        except Exception as e:
            print(f"generate_sales_report error: {e}")
            return pd.DataFrame()

    # ──────────────────────────────────────────────────────────────────────────
    # Waste Management
    # ──────────────────────────────────────────────────────────────────────────
    def validate_waste_entry(self, product: str, quantity: float, unit: str,
                              date_val, reason: str, value: float) -> list:
        errors = []
        if not product:
            errors.append("Product must be selected.")
        if quantity <= 0:
            errors.append("Quantity must be greater than 0.")
        if quantity > 10000:
            errors.append("Quantity seems unrealistically large. Please verify.")
        if unit not in ["kg", "pcs", "liters"]:
            errors.append("Invalid unit selected.")
        if reason not in ["Expired", "Damaged", "Overstock", "Quality Issues",
                           "Customer Return", "Staff Error", "Other"]:
            errors.append("Invalid waste reason.")
        if value < 0:
            errors.append("Value lost cannot be negative.")
        try:
            if hasattr(date_val, "strftime"):
                pass
            else:
                datetime.strptime(str(date_val), "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date format.")
        return errors

    def log_waste_entry(self, store, product, quantity, unit, date_val,
                        reason, value, notes):
        try:
            try:
                df = pd.read_csv(f"{DATA_DIR}/waste_data.csv")
            except FileNotFoundError:
                df = pd.DataFrame(columns=["Date", "Store", "Product", "Category",
                                            "Quantity", "Unit", "Reason", "Value_Lost", "Notes"])
            category = PRODUCTS_META.get(product, {}).get("category", "Other")
            new_row = pd.DataFrame([{
                "Date": str(date_val),
                "Store": store,
                "Product": product,
                "Category": category,
                "Quantity": float(quantity),
                "Unit": unit,
                "Reason": reason,
                "Value_Lost": float(value),
                "Notes": str(notes) if notes else "",
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(f"{DATA_DIR}/waste_data.csv", index=False)
            return True
        except Exception as e:
            print(f"log_waste_entry error: {e}")
            return False

    def calculate_waste_reduction_percentage(self, store: str) -> dict:
        try:
            df = self._load_waste()
            if df.empty:
                return {"current_week": 0, "previous_week": 0, "reduction": 0,
                        "current_value": 0, "previous_value": 0}
            sw = df[df["Store"] == store] if "Store" in df.columns else df
            now = datetime.now()
            cur_start = now - timedelta(days=7)
            prev_start = now - timedelta(days=14)
            cw = sw[sw["Date"] >= cur_start]["Quantity"].sum()
            pw = sw[(sw["Date"] >= prev_start) & (sw["Date"] < cur_start)]["Quantity"].sum()
            cv = sw[sw["Date"] >= cur_start]["Value_Lost"].sum() if "Value_Lost" in sw.columns else 0
            pv = sw[(sw["Date"] >= prev_start) & (sw["Date"] < cur_start)]["Value_Lost"].sum() if "Value_Lost" in sw.columns else 0
            reduction = round(((pw - cw) / max(pw, 1)) * 100, 1)
            return {"current_week": round(float(cw), 2), "previous_week": round(float(pw), 2),
                    "reduction": reduction, "current_value": round(float(cv), 2),
                    "previous_value": round(float(pv), 2)}
        except Exception as e:
            print(f"calculate_waste_reduction_percentage error: {e}")
            return {"current_week": 0, "previous_week": 0, "reduction": 0,
                    "current_value": 0, "previous_value": 0}

    # ──────────────────────────────────────────────────────────────────────────
    # Alerts
    # ──────────────────────────────────────────────────────────────────────────
    def get_restock_alerts(self, store: str) -> list:
        try:
            products_df = self.get_product_list(store)
            if products_df.empty:
                return []
            low = products_df[products_df["Current Stock"] <= products_df["Reorder Level"]]
            alerts = []
            for _, row in low.iterrows():
                ratio = row["Current Stock"] / max(row["Reorder Level"], 1)
                urgency = "HIGH" if ratio < 0.5 else "MEDIUM"
                suggested_order = max(0, int(row["Reorder Level"] * 2.5 - row["Current Stock"]))
                alerts.append({
                    "product": row["Product Name"],
                    "category": row.get("Category", ""),
                    "current_stock": int(row["Current Stock"]),
                    "reorder_level": int(row["Reorder Level"]),
                    "urgency": urgency,
                    "supplier": row.get("Supplier", "N/A"),
                    "suggested_order": suggested_order,
                    "unit_price": float(row.get("Unit Price", 0)),
                })
            return sorted(alerts, key=lambda x: (0 if x["urgency"] == "HIGH" else 1, x["current_stock"]))
        except Exception as e:
            print(f"get_restock_alerts error: {e}")
            return []

    def get_expiry_alerts(self, store: str, days_threshold: int = 3) -> list:
        try:
            products_df = self.get_product_list(store)
            if products_df.empty or "Expiry Date" not in products_df.columns:
                return []
            today = datetime.now().date()
            alerts = []
            for _, row in products_df.iterrows():
                try:
                    exp = datetime.strptime(str(row["Expiry Date"]), "%Y-%m-%d").date()
                    days_left = (exp - today).days
                    if days_left <= days_threshold:
                        severity = "CRITICAL" if days_left <= 1 else ("HIGH" if days_left <= 2 else "MEDIUM")
                        alerts.append({
                            "product": row["Product Name"],
                            "category": row.get("Category", ""),
                            "expiry_date": str(row["Expiry Date"]),
                            "days_left": days_left,
                            "current_stock": int(row.get("Current Stock", 0)),
                            "severity": severity,
                        })
                except Exception:
                    continue
            return sorted(alerts, key=lambda x: x["days_left"])
        except Exception as e:
            print(f"get_expiry_alerts error: {e}")
            return []

    def get_waste_alerts(self, store: str, threshold: float = 70.0) -> list:
        try:
            products_df = self.get_product_list(store)
            if products_df.empty:
                return []
            high_risk = products_df[products_df["Waste Risk %"] > threshold]
            alerts = []
            for _, row in high_risk.iterrows():
                alerts.append({
                    "product": row["Product Name"],
                    "category": row.get("Category", ""),
                    "waste_risk": float(row["Waste Risk %"]),
                    "current_stock": int(row.get("Current Stock", 0)),
                    "severity": "HIGH" if row["Waste Risk %"] > 85 else "MEDIUM",
                })
            return sorted(alerts, key=lambda x: -x["waste_risk"])
        except Exception as e:
            print(f"get_waste_alerts error: {e}")
            return []

    def get_all_alerts_summary(self, store: str) -> dict:
        return {
            "restock": self.get_restock_alerts(store),
            "expiry": self.get_expiry_alerts(store),
            "waste": self.get_waste_alerts(store),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Store summary (used by AI assistant)
    # ──────────────────────────────────────────────────────────────────────────
    def get_store_summary(self, store: str) -> dict:
        try:
            sales_df = self._load_sales()
            ss = sales_df[sales_df["Store"] == store] if not sales_df.empty else pd.DataFrame()
            total = int(ss["Actual_Sales"].sum()) if not ss.empty else 0
            avg = float(ss.groupby("Date")["Actual_Sales"].sum().mean()) if not ss.empty else 0
            top = ss.groupby("Product")["Actual_Sales"].sum().nlargest(3).to_dict() if not ss.empty else {}
            return {"total_sales": total, "avg_daily_sales": round(avg, 1), "top_products": top}
        except Exception as e:
            print(f"get_store_summary error: {e}")
            return {}
