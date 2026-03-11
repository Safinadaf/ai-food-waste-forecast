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
        message: `Hello ${data.name}, your number squared is ${data.number * data.number}`
    };

    res.json(result);
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
