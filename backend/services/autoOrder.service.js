const Product = require('../models/Product');
const Sale = require('../models/Sale');
const Event = require('../models/Event');

/**
 * Recommend orders based on stock, recent demand, waste risk, upcoming events.
 * qty = max(0, ceil(avgDailyDemand * coverDays * eventBoost) - currentStock)
 *   - reduce by waste_risk (don't overstock spoil-prone items)
 */
async function buildAutoOrder(store) {
  const q = store ? { store } : {};
  const products = await Product.find(q).lean();

  // upcoming events in next 7 days
  const today = new Date().toISOString().slice(0, 10);
  const in7 = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  const events = await Event.find({
    date: { $gte: today, $lte: in7 },
    ...(store ? { store } : {})
  }).lean();
  const eventBoost = events.some(e => e.impact === 'High') ? 1.4
                    : events.some(e => e.impact === 'Medium') ? 1.2 : 1.0;

  const recs = [];
  for (const p of products) {
    const recent = await Sale.find({ store: p.store, product: p.name })
      .sort({ date: -1 }).limit(7).lean();
    const avg = recent.length
      ? recent.reduce((s, r) => s + (r.actual_sales || 0), 0) / recent.length
      : p.reorder_level || 10;

    const coverDays = 3;
    const wasteFactor = 1 - Math.min(0.6, (p.waste_risk || 0) / 100);
    const target = Math.ceil(avg * coverDays * eventBoost * wasteFactor);
    const qty = Math.max(0, target - (p.current_stock || 0));

    if (qty > 0) {
      const reasons = [];
      if (p.current_stock <= p.reorder_level) reasons.push('below reorder level');
      if (eventBoost > 1) reasons.push(`upcoming event boost x${eventBoost}`);
      if ((p.waste_risk || 0) >= 50) reasons.push(`high waste risk ${p.waste_risk}% (reduced)`);
      reasons.push(`avg demand ${avg.toFixed(1)}/day`);

      recs.push({
        store: p.store, product: p.name, supplier: p.supplier,
        quantity: qty, unit_price: p.price,
        estimated_cost: +(qty * (p.price || 0)).toFixed(2),
        reason: reasons.join('; ')
      });
    }
  }
  return { generated_at: new Date().toISOString(), event_boost: eventBoost, orders: recs };
}

module.exports = { buildAutoOrder };
