const mongoose = require('mongoose');

// Define the Reservation schema
const Reservation = mongoose.model('Reservation', new mongoose.Schema({
  managerName: String,
  employeeName: String,
  model: String,
  startDate: Date,
  endDate: Date,
  status: { type: String, default: 'reserved' }
}));

// Function to reserve a laptop
function reserveLaptop(req, res) {
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
}

module.exports = { reserveLaptop };
