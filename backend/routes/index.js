const router = require('express').Router();
const products = require('../controllers/products.controller');
const waste = require('../controllers/waste.controller');
const forecast = require('../controllers/forecast.controller');
const alerts = require('../controllers/alerts.controller');
const ai = require('../controllers/aiChat.controller');
const auto = require('../controllers/autoOrder.controller');
const sales = require('../controllers/sales.controller');

// Product routes
router.get('/products', products.list);
router.post('/products/update', products.update);

// Waste routes
router.get('/waste', waste.list);
router.post('/waste', waste.create);
router.delete('/waste/:id', waste.remove);

// Sales routes (was missing entirely)
router.get('/sales', sales.list);
router.post('/sales', sales.create);

// Forecast route
router.get('/forecast', forecast.forecast);

// Alerts route
router.get('/alerts', alerts.list);

// AI Chat route
router.post('/ai-chat', ai.chat);

// Auto-Order route
router.get('/auto-order', auto.get);

// Events route (was missing)
const events = require('../controllers/events.controller');
router.get('/events', events.list);
router.post('/events', events.create);

// Health check
router.get('/health', (_, res) => res.json({ ok: true, ts: Date.now() }));

module.exports = router;
