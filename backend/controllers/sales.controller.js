const Sale = require('../models/Sale');

// GET /api/sales?store=X&product=Y&limit=100
exports.list = async (req, res) => {
  try {
    const { store, product, limit = 200 } = req.query;
    const q = {};
    if (store) q.store = store;
    if (product) q.product = product;
    const items = await Sale.find(q).sort({ date: -1 }).limit(+limit).lean();
    res.json(items);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};

// POST /api/sales
exports.create = async (req, res) => {
  try {
    const { date, store, product, actual_sales, predicted_sales } = req.body;
    if (!date || !store || !product) {
      return res.status(400).json({ error: 'date, store, and product are required' });
    }
    const sale = await Sale.findOneAndUpdate(
      { date, store, product },
      { $set: { actual_sales: actual_sales || 0, predicted_sales: predicted_sales || 0 } },
      { upsert: true, new: true }
    );
    res.status(201).json(sale);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
