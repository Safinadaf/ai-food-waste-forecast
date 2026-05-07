const Product = require('../models/Product');

// GET /api/products?store=X&category=Y
exports.list = async (req, res) => {
  try {
    const { store, category } = req.query;
    const q = {};
    if (store) q.store = store;
    if (category && category !== 'All') q.category = category;
    const items = await Product.find(q).sort({ store: 1, name: 1 }).lean();
    res.json(items);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};

// POST /api/products/update
exports.update = async (req, res) => {
  try {
    const { store, name, ...patch } = req.body;
    if (!store || !name) return res.status(400).json({ error: 'store and name are required' });
    const doc = await Product.findOneAndUpdate(
      { store, name },
      { $set: patch, $setOnInsert: { store, name } },
      { upsert: true, new: true }
    );
    res.json(doc);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
