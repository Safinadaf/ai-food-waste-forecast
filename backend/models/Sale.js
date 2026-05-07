const mongoose = require('mongoose');
const SaleSchema = new mongoose.Schema({
  date: { type: String, required: true },   // YYYY-MM-DD
  store: { type: String, required: true },
  product: { type: String, required: true },
  actual_sales: { type: Number, default: 0 },
  predicted_sales: { type: Number, default: 0 }
}, { timestamps: true });
SaleSchema.index({ store: 1, product: 1, date: 1 });
module.exports = mongoose.model('Sale', SaleSchema);
