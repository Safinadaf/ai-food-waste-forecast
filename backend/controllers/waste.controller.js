const Waste = require('../models/Waste');
const Product = require('../models/Product');

// POST /api/waste
exports.create = async (req, res) => {
  try {
    const { date, store, product, quantity, unit, reason, notes } = req.body;
    if (!date || !store || !product) {
      return res.status(400).json({ error: 'date, store, and product are required' });
    }
    const w = await Waste.create({ date, store, product, quantity, unit, reason, notes });

    // Bump waste_risk for that product (capped at 100)
    await Product.findOneAndUpdate(
      { store, name: product },
      [{ $set: { waste_risk: { $min: [100, { $add: ['$waste_risk', Math.min(5, Math.ceil((quantity || 1)))] }] } } }]
    );
    res.status(201).json(w);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};

// GET /api/waste?store=X
exports.list = async (req, res) => {
  try {
    const { store } = req.query;
    const q = store ? { store } : {};
    res.json(await Waste.find(q).sort({ date: -1 }).limit(200).lean());
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};

// DELETE /api/waste/:id
exports.remove = async (req, res) => {
  try {
    const w = await Waste.findByIdAndDelete(req.params.id);
    if (!w) return res.status(404).json({ error: 'Waste record not found' });
    res.json({ deleted: true, id: req.params.id });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
