const mongoose = require('mongoose');
const EventSchema = new mongoose.Schema({
  name: { type: String, required: true },
  store: String,
  location: String,
  date: { type: String, required: true },
  impact: { type: String, enum: ['Low', 'Medium', 'High'], default: 'Medium' },
  description: String
}, { timestamps: true });
module.exports = mongoose.model('Event', EventSchema);
