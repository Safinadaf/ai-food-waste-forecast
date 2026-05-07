require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const connectDB = require('./config/db');
const routes = require('./routes');

const app = express();

// CORS — allow all origins (adjust for production)
app.use(cors());
app.use(bodyParser.json({ limit: '2mb' }));
app.use(express.urlencoded({ extended: true }));

// API routes
app.use('/api', routes);

// Root health-check
app.get('/', (req, res) => res.json({ status: 'Smart Forecast API running', version: '1.0.0' }));

// Global error handler (must have 4 args to be treated as error middleware)
app.use((err, req, res, _next) => {
  console.error('[ERROR]', err.message);
  res.status(500).json({ error: err.message });
});

const PORT = process.env.PORT || 5000;

connectDB()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`🚀 API running on http://localhost:${PORT}`);
      console.log(`📌 Environment: ${process.env.NODE_ENV || 'development'}`);
    });
  })
  .catch(err => {
    console.error('❌ DB connection failed:', err.message);
    process.exit(1);
  });
