/**
 * Seed MongoDB from CSV/JSON files in ../data
 * Usage: node scripts/seed.js
 */
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const connectDB = require('../config/db');
const Product = require('../models/Product');
const Sale = require('../models/Sale');
const Waste = require('../models/Waste');
const Event = require('../models/Event');

function parseCSV(file) {
  const text = fs.readFileSync(file, 'utf8').replace(/\r/g, '');
  const lines = text.split('\n').filter(l => l.trim().length);
  const headers = lines.shift().split(',').map(h => h.trim());
  return lines.map(line => {
    const cells = line.split(',');
    const row = {};
    headers.forEach((h, i) => row[h] = cells[i]?.trim());
    return row;
  });
}

(async () => {
  await connectDB();
  const dataDir = path.join(__dirname, '..', 'data');

  // Products
  const prodRows = parseCSV(path.join(dataDir, 'product_master.csv'));
  await Product.deleteMany({});
  await Product.insertMany(prodRows.map(r => ({
    store: r['Store'],
    name: r['Product Name'],
    category: r['Category'],
    current_stock: +r['Current Stock'] || 0,
    reorder_level: +r['Reorder Level'] || 0,
    price: +r['Unit Price'] || 0,
    supplier: r['Supplier'],
    status: r['Status'] || 'Active',
    waste_risk: +r['Waste Risk %'] || 0,
  })));
  console.log(`✓ Products: ${prodRows.length}`);

  // Sales
  const saleRows = parseCSV(path.join(dataDir, 'sales_data.csv'));
  await Sale.deleteMany({});
  await Sale.insertMany(saleRows.map(r => ({
    date: r['Date'], store: r['Store'], product: r['Product'],
    actual_sales: +r['Actual_Sales'] || 0,
    predicted_sales: +r['Predicted_Sales'] || 0,
  })));
  console.log(`✓ Sales: ${saleRows.length}`);

  // Waste
  const wasteRows = parseCSV(path.join(dataDir, 'waste_data.csv'));
  await Waste.deleteMany({});
  await Waste.insertMany(wasteRows.map(r => ({
    date: r['Date'], store: r['Store'], product: r['Product'],
    quantity: +r['Quantity'] || 0, unit: r['Unit'], reason: r['Reason']
  })));
  console.log(`✓ Waste: ${wasteRows.length}`);

  // Events
  const events = JSON.parse(fs.readFileSync(path.join(dataDir, 'event_data.json'), 'utf8'));
  await Event.deleteMany({});
  await Event.insertMany(events.map(e => ({
    name: e.name, store: e.store, location: e.location,
    date: e.date, impact: e.impact, description: e.description
  })));
  console.log(`✓ Events: ${events.length}`);

  console.log('\n🌱 Seed complete');
  process.exit(0);
})().catch(e => { console.error(e); process.exit(1); });
