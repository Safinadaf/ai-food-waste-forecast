const Event = require('../models/Event');

// GET /api/events?store=X
exports.list = async (req, res) => {
  try {
    const { store } = req.query;
    const q = store ? { store } : {};
    const items = await Event.find(q).sort({ date: 1 }).lean();
    res.json(items);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};

// POST /api/events
exports.create = async (req, res) => {
  try {
    const { name, store, location, date, impact, description } = req.body;
    if (!name || !date) return res.status(400).json({ error: 'name and date are required' });
    const ev = await Event.create({ name, store, location, date, impact, description });
    res.status(201).json(ev);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
