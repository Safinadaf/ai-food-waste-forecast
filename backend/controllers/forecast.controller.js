const Sale = require('../models/Sale');
const Product = require('../models/Product');
const { runPython } = require('../services/python.service');

exports.forecast = async (req, res) => {
  try {
    const { store } = req.query;
    if (!store) return res.status(400).json({ error: 'store query parameter is required' });

    const [sales, products] = await Promise.all([
      Sale.find({ store }).sort({ date: 1 }).lean(),
      Product.find({ store }).lean()
    ]);

    try {
      const out = await runPython('forecast.py', { store, sales, products });
      return res.json(out);
    } catch (pythonErr) {
      // JS fallback forecasting when Python is unavailable
      const byProduct = {};
      sales.forEach(s => {
        (byProduct[s.product] ||= []).push(s.actual_sales || 0);
      });

      const forecasts = products.map(p => {
        const hist = byProduct[p.name] || [];
        const avg = hist.length
          ? hist.reduce((a, b) => a + b, 0) / hist.length
          : Math.max(p.reorder_level || 10, 10);

        // Simple trend: last 3 vs previous 3
        let trend = 1.0;
        if (hist.length >= 6) {
          const last3 = hist.slice(-3).reduce((a, b) => a + b, 0) / 3;
          const prev3 = hist.slice(-6, -3).reduce((a, b) => a + b, 0) / 3 || 1;
          trend = Math.max(0.5, Math.min(1.5, last3 / prev3));
        }

        const predicted = Math.round(avg * 1.05 * trend);
        return {
          product: p.name,
          current_stock: p.current_stock || 0,
          reorder_level: p.reorder_level || 0,
          avg_daily_demand: Math.round(avg * 100) / 100,
          trend_factor: Math.round(trend * 100) / 100,
          predicted_demand: predicted,
          shortfall: Math.max(0, predicted - (p.current_stock || 0))
        };
      });

      return res.json({ store, forecasts, fallback: true, error: pythonErr.message });
    }
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
