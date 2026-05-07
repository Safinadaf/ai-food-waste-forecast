"""
ai_chat.py — Fixed AIAssistant
Fixes:
 - Robust API detection and initialization
 - Detailed, context-aware demo responses
 - Proper error handling without exposing stack traces
 - get_store_context reads from correct paths
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env file from the backend directory (assuming it's shared)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', '.env'))


class AIAssistant:
    def __init__(self):
        self.api_provider = self._detect_provider()
        self.client = self._init_client()

    def _detect_provider(self) -> str:
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            return "gemini"
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        return "demo"

    def _init_client(self):
        if self.api_provider == "gemini":
            try:
                import google.generativeai as genai
                key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                genai.configure(api_key=key)
                return genai.GenerativeModel("gemini-1.5-flash")
            except ImportError:
                try:
                    from google import genai as new_genai
                    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                    return new_genai.Client(api_key=key)
                except ImportError:
                    self.api_provider = "demo"
                    return None
        if self.api_provider == "openai":
            try:
                from openai import OpenAI
                return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except ImportError:
                self.api_provider = "demo"
                return None
        return None

    # ── Context builder ───────────────────────────────────────────────────────
    def get_store_context(self, store: str) -> dict:
        ctx = {"store": store, "date": str(datetime.now().date()),
               "sales_data": {}, "waste_data": {}, "events": [],
               "inventory": {}}
        # Sales
        try:
            df = pd.read_csv("data/sales_data.csv")
            ss = df[df["Store"] == store] if "Store" in df.columns else df
            ss = ss[pd.to_datetime(ss["Date"]) >= datetime.now() - timedelta(days=7)]
            if not ss.empty:
                ctx["sales_data"] = {
                    "total_recent_sales": int(ss["Actual_Sales"].sum()),
                    "avg_daily_sales": round(float(ss.groupby("Date")["Actual_Sales"].sum().mean()), 1),
                    "top_products": ss.groupby("Product")["Actual_Sales"].sum().nlargest(5).to_dict()
                    if "Product" in ss.columns else {}
                }
        except Exception:
            pass
        # Waste
        try:
            df = pd.read_csv("data/waste_data.csv")
            sw = df[df["Store"] == store] if "Store" in df.columns else df
            cutoff = str((datetime.now() - timedelta(days=7)).date())
            sw = sw[sw["Date"] >= cutoff] if "Date" in sw.columns else sw
            if not sw.empty:
                ctx["waste_data"] = {
                    "total_recent_waste_kg": round(float(sw["Quantity"].sum()), 2),
                    "most_wasted_products": sw.groupby("Product")["Quantity"].sum().nlargest(5).to_dict()
                    if "Product" in sw.columns else {},
                    "waste_reasons": sw["Reason"].value_counts().to_dict() if "Reason" in sw.columns else {},
                    "total_value_lost": round(float(sw["Value_Lost"].sum()), 2)
                    if "Value_Lost" in sw.columns else 0,
                }
        except Exception:
            pass
        # Inventory
        try:
            df = pd.read_csv("data/product_master.csv")
            sp = df[df["Store"] == store] if "Store" in df.columns else df
            if not sp.empty:
                low = sp[sp["Current Stock"] <= sp["Reorder Level"]]
                ctx["inventory"] = {
                    "total_products": len(sp),
                    "low_stock_count": len(low),
                    "low_stock_items": low["Product Name"].tolist()[:5] if "Product Name" in low.columns else [],
                }
        except Exception:
            pass
        # Events
        try:
            with open("data/event_data.json") as f:
                events = json.load(f)
            cutoff_date = (datetime.now() - timedelta(days=30)).date()
            ctx["events"] = [
                e for e in events
                if (not e.get("store") or e["store"] == store) and
                datetime.strptime(e["date"], "%Y-%m-%d").date() >= cutoff_date
            ][:5]
        except Exception:
            pass
        return ctx

    # ── Response generation ───────────────────────────────────────────────────
    def _system_prompt(self, ctx: dict) -> str:
        return (
            "You are an expert AI assistant for a smart food waste management system. "
            "You help retail store managers reduce food waste, optimize inventory, and boost profitability.\n\n"
            f"Current Context:\n"
            f"- Store: {ctx.get('store', 'Unknown')}\n"
            f"- Date: {ctx.get('date')}\n"
            f"- Recent Sales (7d): {json.dumps(ctx.get('sales_data', {}))}\n"
            f"- Recent Waste (7d): {json.dumps(ctx.get('waste_data', {}))}\n"
            f"- Inventory Status: {json.dumps(ctx.get('inventory', {}))}\n"
            f"- Upcoming Events: {json.dumps(ctx.get('events', []))}\n\n"
            "Provide actionable, data-driven insights. Be concise, friendly, and practical. "
            "Use emojis sparingly. Always tie recommendations to the actual data provided."
        )

    def get_response(self, user_message: str, context_data: dict) -> str:
        if not user_message or not user_message.strip():
            return "Please type a question so I can help you!"

        sys_prompt = self._system_prompt(context_data)

        if self.api_provider == "gemini" and self.client is not None:
            try:
                if hasattr(self.client, "models"):
                    resp = self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"{sys_prompt}\n\nUser: {user_message}"
                    )
                else:
                    resp = self.client.generate_content(
                        f"{sys_prompt}\n\nUser: {user_message}"
                    )
                return resp.text or "I couldn't generate a response. Please try again."
            except Exception as e:
                return self._demo_response(user_message, context_data)

        if self.api_provider == "openai" and self.client is not None:
            try:
                resp = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": sys_prompt},
                               {"role": "user", "content": user_message}],
                    max_tokens=600
                )
                return resp.choices[0].message.content
            except Exception:
                return self._demo_response(user_message, context_data)

        return self._demo_response(user_message, context_data)

    def _demo_response(self, user_message: str, ctx: dict) -> str:
        msg = user_message.lower()
        store = ctx.get("store", "your store")
        waste = ctx.get("waste_data", {})
        sales = ctx.get("sales_data", {})
        inv = ctx.get("inventory", {})

        top_waste = list(waste.get("most_wasted_products", {}).keys())
        top_sales = list(sales.get("top_products", {}).keys())
        low_stock = inv.get("low_stock_items", [])
        total_waste_kg = waste.get("total_recent_waste_kg", 0)
        value_lost = waste.get("total_value_lost", 0)

        if any(k in msg for k in ["waste tomorrow", "go to waste", "expir", "perish"]):
            items = ", ".join(top_waste[:3]) if top_waste else "lettuce, bananas, and tomatoes"
            return (
                f"🔍 **Waste Risk Forecast for {store}:**\n\n"
                f"Based on the last 7 days, **{items}** have the highest waste risk.\n\n"
                f"**Recommendations:**\n"
                f"• Reduce order quantities for these by 10–15%\n"
                f"• Apply markdown pricing on items approaching expiry\n"
                f"• Move high-risk items to front-of-shelf (FIFO method)\n"
                f"• Consider bundling promotions to clear excess stock"
            )

        if "pattern" in msg and "waste" in msg:
            reasons = waste.get("waste_reasons", {})
            top_reason = list(reasons.keys())[0] if reasons else "over-ordering"
            return (
                f"📊 **Waste Patterns for {store} (Last 7 Days):**\n\n"
                f"• Total waste: **{total_waste_kg:.1f} kg** (${value_lost:.2f} value lost)\n"
                f"• Top waste cause: **{top_reason}**\n"
                f"• Most wasted items: {', '.join(top_waste[:3]) if top_waste else 'N/A'}\n\n"
                f"**Action:** Focus on '{top_reason}' to cut waste by 20–30% this week."
            )

        if "reduce" in msg or "cut" in msg:
            return (
                "💡 **Top Strategies to Reduce Food Waste:**\n\n"
                "1. 📉 **Reduce order quantities** for high-risk items by 10–15%\n"
                "2. 🌡️ **Check storage temperatures** — improper temp is a top cause\n"
                "3. 📦 **Apply FIFO** — move older stock to the front daily\n"
                "4. 🏷️ **Markdown pricing** — discount items 2 days before expiry\n"
                "5. 📊 **Use Forecast Dashboard** — align orders with predicted demand\n"
                "6. ⚠️ **Check Alerts daily** — act on expiry and waste alerts early\n"
                "7. 🤝 **Donate near-expiry items** — reduces waste & builds goodwill"
            )

        if any(k in msg for k in ["reorder", "stock", "order more", "low stock"]):
            items_str = ", ".join(low_stock[:3]) if low_stock else "check the Alerts tab"
            return (
                f"📦 **Restock Recommendations for {store}:**\n\n"
                f"• {inv.get('low_stock_count', 0)} items are currently at or below reorder level\n"
                f"• Priority items: **{items_str}**\n\n"
                f"Go to **⚠️ Alerts & Monitoring → Restock Alerts** for a full list with suggested order quantities."
            )

        if any(k in msg for k in ["forecast", "predict", "demand", "sales tomorrow"]):
            avg = sales.get("avg_daily_sales", 0)
            top = ", ".join(top_sales[:3]) if top_sales else "N/A"
            return (
                f"📈 **Demand Forecast Insights for {store}:**\n\n"
                f"• 7-day average daily sales: **{avg:,.0f} units**\n"
                f"• Top-selling products: **{top}**\n\n"
                f"Navigate to **📊 Forecast Dashboard** for detailed per-product predictions "
                f"with confidence scores and waste risk indicators."
            )

        if "event" in msg:
            events = ctx.get("events", [])
            if events:
                e = events[0]
                return (
                    f"📅 **Upcoming Event:** {e.get('name')} on {e.get('date')}\n"
                    f"• Impact: **{e.get('impact', 'Medium')}**\n"
                    f"• Location: {e.get('location', 'N/A')}\n\n"
                    f"For **High** impact events, increase orders by 25–40%.\n"
                    f"For **Medium** impact, increase by 10–20%."
                )
            return "📅 No upcoming events found for your store. Add events in the system to get demand impact forecasts."

        if any(k in msg for k in ["summary", "overview", "how am i doing", "performance"]):
            return (
                f"📋 **Store Performance Summary — {store}:**\n\n"
                f"**Sales (Last 7 Days):**\n"
                f"• Total: {sales.get('total_recent_sales', 0):,} units\n"
                f"• Avg Daily: {sales.get('avg_daily_sales', 0):,.0f} units\n\n"
                f"**Waste (Last 7 Days):**\n"
                f"• Total waste: {total_waste_kg:.1f} kg\n"
                f"• Value lost: ${value_lost:.2f}\n\n"
                f"**Inventory:**\n"
                f"• {inv.get('total_products', 0)} products tracked\n"
                f"• {inv.get('low_stock_count', 0)} items need restocking"
            )

        # Generic
        return (
            f"👋 Hello! I'm your AI assistant for **{store}**. Here's what I can help with:\n\n"
            f"• 🗑️ **Waste analysis** — 'What products might go to waste?'\n"
            f"• 📈 **Sales insights** — 'How are my sales this week?'\n"
            f"• 📦 **Restock help** — 'What should I reorder today?'\n"
            f"• 💡 **Waste reduction** — 'How can I reduce food waste?'\n"
            f"• 📅 **Event impacts** — 'Are there any upcoming events?'\n"
            f"• 📋 **Store summary** — 'Give me a performance overview'\n\n"
            f"*Running in demo mode. Set `GEMINI_API_KEY` or `OPENAI_API_KEY` for full AI responses.*"
        )
