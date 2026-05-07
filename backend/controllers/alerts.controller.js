const { getAlerts } = require('../services/alerts.service');

exports.list = async (req, res) => {
  try {
    const alerts = await getAlerts(req.query.store);
    res.json(alerts);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
};
