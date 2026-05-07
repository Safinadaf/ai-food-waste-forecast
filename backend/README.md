# Smart Forecast Backend

Node.js + Express + MongoDB backend for the AI-Powered Smart Forecasting Streamlit app.
Calls Python `ForecastEngine` and `AIAssistant` via `child_process`.

## 1. Install

```bash
cd backend
npm install
cp .env.example .env       # edit MONGO_URI / API keys
pip install pandas         # only needed if you extend the python scripts
# Optional AI keys (else demo mode):
#   GEMINI_API_KEY=... or OPENAI_API_KEY=...
```

Make sure MongoDB is running locally (`mongod`) **or** point `MONGO_URI` at MongoDB Atlas.

## 2. Seed the database

```bash
npm run seed
```
Loads `data/product_master.csv`, `sales_data.csv`, `waste_data.csv`, `event_data.json`
into MongoDB collections: `products`, `sales`, `wastes`, `events`.

## 3. Run

```bash
npm start          # http://localhost:5000
```

## 4. API Endpoints

| Method | Path                    | Purpose                                  |
|--------|-------------------------|------------------------------------------|
| GET    | `/api/products`         | `?store=...&category=...`                |
| POST   | `/api/products/update`  | upsert by `{store, name, ...patch}`      |
| GET    | `/api/waste`            | `?store=...`                             |
| POST   | `/api/waste`            | log waste; auto-bumps `waste_risk`       |
| GET    | `/api/forecast`         | `?store=...` → calls Python ForecastEngine |
| GET    | `/api/alerts`           | low-stock + high-waste-risk alerts        |
| POST   | `/api/ai-chat`          | `{store, message, history}` → Python AIAssistant |
| GET    | `/api/auto-order`       | `?store=...` → recommended orders         |
| GET    | `/api/health`           | health check                              |

### Example queries

```bash
curl "http://localhost:5000/api/products?store=Store%20A%20-%20Downtown"

curl -X POST http://localhost:5000/api/waste \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-03-15","store":"Store A - Downtown","product":"Bananas","quantity":5,"unit":"kg","reason":"Overripe"}'

curl "http://localhost:5000/api/forecast?store=Store%20A%20-%20Downtown"

curl "http://localhost:5000/api/auto-order?store=Store%20A%20-%20Downtown"

curl -X POST http://localhost:5000/api/ai-chat \
  -H "Content-Type: application/json" \
  -d '{"store":"Store A - Downtown","message":"Which products should I reorder today?"}'
```

## 5. Auto-Order Logic

For each product:
```
avg          = mean(actual_sales of last 7 sale rows)  # fallback: reorder_level
eventBoost   = 1.4 if any High-impact event in next 7d else 1.2 if Medium else 1.0
wasteFactor  = 1 - min(0.6, waste_risk/100)            # don't overstock spoil-prone items
target       = ceil(avg * 3 days * eventBoost * wasteFactor)
quantity     = max(0, target - current_stock)
```

## 6. Streamlit Integration (do NOT change UI — just swap the calls)

Replace any local function calls inside `app.py` with HTTP calls:

```python
import requests, os
API = os.getenv("API_URL", "http://localhost:5000/api")

# Forecast tab
forecast = requests.get(f"{API}/forecast", params={"store": selected_store}).json()
forecast_df = pd.DataFrame(forecast["forecasts"])

# AI Assistant tab
resp = requests.post(f"{API}/ai-chat", json={
    "store": selected_store,
    "message": user_input,
    "history": st.session_state.chat_history,
}).json()
st.write(resp["reply"])

# Auto-order
orders = requests.get(f"{API}/auto-order", params={"store": selected_store}).json()

# Alerts
alerts = requests.get(f"{API}/alerts", params={"store": selected_store}).json()

# Log waste
requests.post(f"{API}/waste", json={
    "date": str(date), "store": selected_store, "product": product,
    "quantity": qty, "unit": unit, "reason": reason
})
```

## 7. Folder structure

```
backend/
├── config/db.js
├── models/        Product, Sale, Waste, Event
├── controllers/   products, waste, forecast, alerts, aiChat, autoOrder
├── routes/index.js
├── services/      python.service, alerts.service, autoOrder.service
├── python/        forecast.py, ai_chat.py
├── scripts/seed.js
├── data/          seed CSV/JSON
├── server.js
├── package.json
└── .env.example
```
