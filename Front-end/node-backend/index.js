const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(bodyParser.json());

// Health check endpoint (fixed: was /api/health but Streamlit was calling it as POST)
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        message: 'Node.js backend is running',
        system: 'AI Smart Forecast Backend',
        timestamp: new Date().toISOString()
    });
});

// Main data endpoint (accepts POST from Streamlit)
app.post('/api/data', (req, res) => {
    const { name, number } = req.body || {};
    const result = {
        message: `Hello ${name || 'User'}. Based on current demand analysis, sales may increase by ${number || 0}% tomorrow.`,
        recommendation: 'Consider increasing stock for high demand products like milk, bread, and bananas.',
        system: 'AI Smart Forecast Backend',
        timestamp: new Date().toISOString()
    };
    console.log('POST /api/data received:', req.body);
    res.json(result);
});

// Also handle POST to /api/health (was breaking the Streamlit form)
app.post('/api/health', (req, res) => {
    const { name, number } = req.body || {};
    const result = {
        status: 'ok',
        message: `Hello ${name || 'User'}. Based on current demand analysis, sales may increase by ${number || 0}% tomorrow.`,
        recommendation: 'Consider increasing stock for high demand products like milk, bread, and bananas.',
        system: 'AI Smart Forecast Backend',
        timestamp: new Date().toISOString()
    };
    console.log('POST /api/health received:', req.body);
    res.json(result);
});

// Catch-all 404
app.use((req, res) => {
    res.status(404).json({ error: `Route ${req.method} ${req.path} not found` });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`✅ Node.js backend running at http://localhost:${PORT}`);
    console.log(`   Health check: GET http://localhost:${PORT}/api/health`);
    console.log(`   Data endpoint: POST http://localhost:${PORT}/api/data`);
});
