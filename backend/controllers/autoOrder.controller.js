const { buildAutoOrder } = require('../services/autoOrder.service');

exports.get = async (req, res) => {
  try {
    const result = await buildAutoOrder(req.query.store);
    res.json(result);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
