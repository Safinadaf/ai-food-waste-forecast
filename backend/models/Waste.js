const mongoose = require('mongoose');
const WasteSchema = new mongoose.Schema({
  date: { type: String, required: true },
  store: { type: String, required: true },
  product: { type: String, required: true },
  quantity: { type: Number, default: 0 },
  unit: { type: String, default: 'kg' },
  reason: String,
  notes: String
}, { timestamps: true });
module.exports = mongoose.model('Waste', WasteSchema);
