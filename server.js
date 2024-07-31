const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const { PythonShell } = require('python-shell');

const app = express();
const port = 3000;

app.use(bodyParser.json());
app.use(express.static('public'));

mongoose.connect('mongodb://localhost:27017/LAMP', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

const Employee = mongoose.model('Employee', new mongoose.Schema({
  name: String,
  role: String,
  email: String,
  dateJoined: Date,
}));

const Laptop = mongoose.model('Laptop', new mongoose.Schema({
  serialNumber: String,
  model: String,
  assignedTo: String,
  status: String,
  location: String,
  lastServiced: Date,
}));

const Reservation = mongoose.model('Reservation', new mongoose.Schema({
  managerName: String,
  employeeName: String,
  model: String,
  startDate: Date,
  endDate: Date,
  status: { type: String, default: 'reserved' }
}));

// API route for assigning laptops
app.post('/api/assignLaptop', (req, res) => {
  const { employeeName } = req.body;

  PythonShell.run('assign_laptop.py', { args: [employeeName] }, (err, result) => {
    if (err) {
      console.error('Error running assign_laptop.py:', err);
      res.status(500).send({ error: 'An error occurred while assigning the laptop.' });
      return;
    }

    const output = result.join('\n');
    console.log('Python script output:', output); // Debugging line

    res.send(output); // Send the result to the frontend
  });
});

// API route for reserving laptops
app.post('/api/reserve_laptop', (req, res) => {
  const { managerName, employeeName, model, startDate, endDate } = req.body;

  const newReservation = new Reservation({
    managerName,
    employeeName,
    model,
    startDate,
    endDate
  });

  newReservation.save((err, reservation) => {
    if (err) {
      console.error('Error reserving laptop:', err);
      res.status(500).send({ error: 'An error occurred while reserving the laptop.' });
      return;
    }
    res.send(`Laptop model ${model} reserved for ${employeeName} by ${managerName} from ${startDate} to ${endDate}`);
  });
});

// API route for predictive maintenance
app.get('/api/predictMaintenance', (req, res) => {
  PythonShell.run('predict_maintenance.py', null, (err, result) => {
    if (err) {
      console.error('Error running predict_maintenance.py:', err);
      res.status(500).send({ error: 'An error occurred while predicting maintenance needs.' });
      return;
    }

    // Process the result (assuming it's JSON data)
    try {
      const predictions = JSON.parse(result.join('\n'));
      res.json(predictions);
    } catch (parseError) {
      console.error('Error parsing predict_maintenance.py result:', parseError);
      res.status(500).send({ error: 'An error occurred while processing maintenance predictions.' });
    }
  });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
