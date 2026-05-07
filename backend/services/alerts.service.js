const Product = require('../models/Product');

async function getAlerts(store) {
  const q = store ? { store } : {};
  const products = await Product.find(q).lean();
  const alerts = [];
  for (const p of products) {
    if (p.current_stock <= p.reorder_level) {
      alerts.push({
        type: 'LOW_STOCK', severity: 'high',
        store: p.store, product: p.name,
        message: `${p.name} low at ${p.store} (${p.current_stock}/${p.reorder_level})`
      });
    }
    if ((p.waste_risk || 0) >= 70) {
      alerts.push({
        type: 'HIGH_WASTE_RISK', severity: 'high',
        store: p.store, product: p.name,
        message: `${p.name} waste risk ${p.waste_risk}% at ${p.store}`
      });
    } else if ((p.waste_risk || 0) >= 40) {
      alerts.push({
        type: 'MEDIUM_WASTE_RISK', severity: 'medium',
        store: p.store, product: p.name,
        message: `${p.name} waste risk ${p.waste_risk}% at ${p.store}`
      });
    }
  }
  return alerts;
}
module.exports = { getAlerts };
