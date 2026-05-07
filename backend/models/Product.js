const mongoose = require('mongoose');
const ProductSchema = new mongoose.Schema({
  name: { type: String, required: true },
  category: String,
  store: { type: String, required: true },
  current_stock: { type: Number, default: 0 },
  reorder_level: { type: Number, default: 0 },
  price: { type: Number, default: 0 },
  supplier: String,
  status: { type: String, default: 'Active' },
  waste_risk: { type: Number, default: 0 } // %
}, { timestamps: true });
ProductSchema.index({ store: 1, name: 1 }, { unique: true });
module.exports = mongoose.model('Product', ProductSchema);
