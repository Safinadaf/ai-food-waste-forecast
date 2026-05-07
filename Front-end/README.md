# 🧠 AI-Powered Smart Forecasting for Zero Food Waste

A comprehensive retail inventory management and food waste reduction platform built with **Streamlit (Python)** and a lightweight **Node.js** backend.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+ (optional, for the backend endpoint in AI tab)

---

### Step 1 — Clone / Extract the Project

```bash
# Extract the ZIP and navigate into the Front-end folder
cd Front-end
```

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Generate Realistic Dummy Data

```bash
python generate_data.py
```

This creates `data/sales_data.csv`, `data/waste_data.csv`, `data/product_master.csv`, and `data/event_data.json` with 90 days of realistic data across all 4 stores.

### Step 4 — Run the Streamlit App

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

### Step 5 — (Optional) Run the Node.js Backend

```bash
cd node-backend
npm install
npm start
```

The backend runs at **http://localhost:5000** and powers the "Node.js Backend Interaction" panel in the AI Assistant tab.

---

### Step 6 — (Optional) Enable Full AI Responses

Create a `.env` file (or set environment variables) with your AI API key:

```bash
# For Google Gemini (recommended, free tier available)
GEMINI_API_KEY=your_key_here

# OR for OpenAI
OPENAI_API_KEY=your_key_here
```

Then install the AI SDK:
```bash
pip install google-generativeai   # for Gemini
# OR
pip install openai                 # for OpenAI
```

The app works in **Demo Mode** without any API key — providing context-aware responses based on real data.

---

## 🗂️ Project Structure

```
Front-end/
├── app.py                  ← Main Streamlit application
├── generate_data.py        ← Realistic dummy data generator
├── requirements.txt        ← Python dependencies
├── .env                    ← Environment variables (AI keys)
├── utils/
│   ├── __init__.py
│   ├── forecast.py         ← ForecastEngine (all analytics + CRUD)
│   └── ai_chat.py          ← AIAssistant (Gemini/OpenAI/Demo)
├── data/
│   ├── sales_data.csv      ← 90-day sales history (auto-generated)
│   ├── waste_data.csv      ← 90-day waste history (auto-generated)
│   ├── product_master.csv  ← Product catalog for all stores
│   └── event_data.json     ← Local events data
└── node-backend/
    ├── index.js            ← Express.js API server
    └── package.json
```

---

## 📋 Modules & Features

### 📦 Product Management
- View/filter products by category, waste risk, stock status
- Inline editing of stock, price, supplier, expiry date
- Add new products with full validation:
  - Empty field checks
  - Negative stock prevention
  - Duplicate product detection
  - Invalid expiry date detection
  - Category validation
- Works correctly for all 4 stores (A, B, C, D)

### 📊 Forecast Dashboard
- Period options: **Today, Tomorrow, Next 3 Days, Next Week, Monthly, Yearly** — all working
- Deterministic AI predictions (no flickering on rerun)
- Manual override column
- Waste risk + confidence score per product
- Save, finalize, send, and download forecast
- Historical accuracy tracking

### 📈 Analytics & Reports
- Sales Report, Waste Report, Combined Report
- All time periods: Daily, Weekly, Monthly, Yearly
- Dynamic charts: area trend, bar, pie, scatter, dual-axis
- KPI row: today's sales, weekly sales, waste metrics
- Category breakdown and top products
- CSV report download

### 🗑️ Waste Management
- Log waste with full validation (quantity > 0, valid reason, future-date check, etc.)
- Waste reduction progress (this week vs last week)
- Value lost tracking
- Multi-chart analytics: pie, bar by reason, category breakdown
- 30-day waste heatmap
- Store-wise waste comparison
- Export waste history as CSV

### ⚠️ Alerts & Monitoring
- **Restock Alerts**: HIGH/MEDIUM urgency, with suggested order quantities
- **Expiry Alerts**: CRITICAL/HIGH/MEDIUM, configurable days threshold
- **Waste Risk Alerts**: configurable threshold
- Color-coded styled tables
- Purchase Order generation & download
- Configurable thresholds and notification settings

### 🤖 AI Assistant
- Context-aware responses using real store data
- Supports Gemini, OpenAI, or Demo mode
- 8 quick-question shortcuts
- Full chat history
- Covers: waste prediction, waste patterns, reorder advice, sales forecast, events, store summary

---

## 🐛 All Bugs Fixed (vs Original)

| # | Issue | Fix |
|---|-------|-----|
| 1 | Forecast period only showed "Today" (period param ignored) | Full period-to-date-range mapping implemented |
| 2 | Random forecasts changed on every Streamlit rerun | Deterministic seeding per (store, product, period, date) |
| 3 | Product Management — no validation on Add Product | Full validation: empty fields, negatives, duplicates, invalid expiry |
| 4 | `save_product_updates` corrupted other stores' data | Fixed to only overwrite current store's rows |
| 5 | Analytics charts crashed when columns missing | Added defensive column checks throughout |
| 6 | `get_combined_analytics` merge failed (wrong key) | Fixed to use period-correct join key |
| 7 | Waste log form accepted 0 quantity | Validation: quantity > 0 required |
| 8 | AI chat quick-buttons didn't trigger responses | Fixed `pending_prompt` pattern with `st.rerun()` |
| 9 | Node.js backend endpoint mismatch (POST to `/api/health`) | Added POST handler for `/api/health` |
| 10 | Alerts showed 0 for all stores (data not loading) | Fixed `get_product_list` to correctly load per-store data |
| 11 | Expiry alerts not generated | Added `get_expiry_alerts()` with per-product expiry date |
| 12 | Waste alerts not generated | Added `get_waste_alerts()` with configurable threshold |
| 13 | Charts had no data for Store B, C, D | `generate_data.py` creates data for all 4 stores |
| 14 | `get_sales_analytics` Yearly period missing | Added Yearly aggregation |
| 15 | `forecast_edits` reset every rerun | Added `last_period_key` guard |
| 16 | Waste data missing `Value_Lost`, `Category` columns | Updated schema and generator |
| 17 | AI `get_store_context` read wrong paths | Fixed paths to match `data/` directory |
| 18 | Analytics Report missing KPI summary row | Added 4-metric KPI bar at top |
| 19 | No store-wise waste comparison chart | Added `get_store_waste_comparison()` |
| 20 | Missing `utils/__init__.py` | Added |

---

## 🔧 Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key (optional) |
| `OPENAI_API_KEY` | OpenAI API key (optional) |
| `API_BASE_URL` | Node.js backend URL (default: `http://localhost:5000/api`) |
