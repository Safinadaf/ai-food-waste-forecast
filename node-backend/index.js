const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');

const app = express();
app.use(cors()); // allow cross-origin requests from Streamlit
app.use(bodyParser.json());

app.post('/api/data', (req, res) => {
    const data = req.body;
    console.log("Received from Streamlit:", data);

    // Process or compute something
    const result = {
    message: `Hello ${data.name}. Based on current demand analysis, sales may increase by ${data.number}% tomorrow.`,
    recommendation: "Consider increasing stock for high demand products like milk, bread, and bananas.",
    system: "AI Smart Forecast Backend"
    };

    res.json(result);
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
