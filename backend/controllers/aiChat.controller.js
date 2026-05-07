const { runPython } = require('../services/python.service');
const Product = require('../models/Product');
const Sale = require('../models/Sale');
const Waste = require('../models/Waste');
const Event = require('../models/Event');

exports.chat = async (req, res) => {
  try {
    const { store, message, history = [] } = req.body;
    if (!message) return res.status(400).json({ error: 'message is required' });

    const [products, sales, waste, events] = await Promise.all([
      Product.find(store ? { store } : {}).lean(),
      Sale.find(store ? { store } : {}).sort({ date: -1 }).limit(50).lean(),
      Waste.find(store ? { store } : {}).sort({ date: -1 }).limit(50).lean(),
      Event.find(store ? { store } : {}).lean()
    ]);

    try {
      const out = await runPython('ai_chat.py', {
        store, message, history,
        context: { products, sales, waste, events }
      });
      return res.json(out);
    } catch (pythonErr) {
      // Graceful JS fallback when Python/API is unavailable
      return res.json({
        reply: `(demo mode) You asked: "${message}". For ${store || 'all stores'} I see ${products.length} products, ${sales.length} recent sales rows, ${waste.length} waste records, and ${events.length} events.`,
        provider: 'demo',
        error: pythonErr.message
      });
    }
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
