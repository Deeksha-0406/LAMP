require('dotenv').config(); // Load environment variables from .env file

const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const app = express();
app.use(bodyParser.json());

// Database connection
mongoose.connect(process.env.MONGO_URI, { useNewUrlParser: true, useUnifiedTopology: true })
    .then(() => console.log('Connected to MongoDB'))
    .catch(err => console.error('Failed to connect to MongoDB', err));

// Define schemas
const employeeSchema = new mongoose.Schema({
    name: String,
    role: String,
    email: String,
    dateJoined: Date,
    // Other fields as needed
});

const laptopSchema = new mongoose.Schema({
    serialNumber: String,
    model: String,
    brand: String,
    specifications: {
        cpu: String,
        ram: String,
        storage: String,
        graphics: String,
    },
    status: String, // Available, Assigned, Reserved, etc.
    location: String,
    lastServiced: Date,
});

const reservationSchema = new mongoose.Schema({
    employeeId: mongoose.Schema.Types.ObjectId,
    laptopId: mongoose.Schema.Types.ObjectId,
    reservedDate: Date,
    status: String // Reserved, Active, etc.
});

const assignmentSchema = new mongoose.Schema({
    employeeId: mongoose.Schema.Types.ObjectId,
    laptopId: mongoose.Schema.Types.ObjectId,
    assignedDate: Date,
    returnedDate: Date,
    status: String // Active, Completed, etc.
});

const Employee = mongoose.model('Employee', employeeSchema);
const Laptop = mongoose.model('Laptop', laptopSchema);
const Reservation = mongoose.model('Reservation', reservationSchema);
const Assignment = mongoose.model('Assignment', assignmentSchema);

// Load model (assuming you're using a Python script for this)
let model;
try {
    const pythonScript = path.join(__dirname, 'load_model.py');
    const modelPath = path.join(__dirname, 'laptop_recommendation_model.pkl');
    
    // Execute the Python script to load the model
    // This is a placeholder; replace with actual logic to use your model
    const result = execSync(`python ${pythonScript} ${modelPath}`).toString();
    model = JSON.parse(result); // Assumes Python script returns model as JSON string
} catch (error) {
    console.error('Failed to load model:', error);
}

// API routes
app.post('/api/recommendations', async (req, res) => {
    try {
        const { name } = req.body;
        if (!name) return res.status(400).json({ error: 'Employee name is required' });

        const employee = await Employee.findOne({ name });
        if (!employee) return res.status(404).json({ error: 'Employee not found' });

        let laptop;
        // Fetch an available laptop
        laptop = await Laptop.findOne({ status: 'Available' });
        if (!laptop) return res.status(404).json({ error: 'No available laptop found' });

        const employeeFeatures = {
            role: employee.role,
            experienceLevel: employee.experienceLevel || '', // Ensure it matches your model's expected input
            age: employee.age || 0, // Default value if not available
            cpu: laptop.specifications.cpu,
            ram: laptop.specifications.ram,
            storage: laptop.specifications.storage,
            graphics: laptop.specifications.graphics
        };

        // Call to a function or service that uses the model to make predictions
        const prediction = await predictWithModel(employeeFeatures); // This function should be implemented

        laptop = await Laptop.findById(prediction.laptopId);
        if (!laptop) return res.status(404).json({ error: 'No laptop found for the recommendation' });

        // Update laptop status
        await Laptop.updateOne({ _id: laptop._id }, { status: 'Assigned' });

        // Create a new assignment entry
        const newAssignment = new Assignment({
            employeeId: employee._id,
            laptopId: laptop._id,
            assignedDate: new Date(),
            returnedDate: null,
            status: 'Active'
        });
        await newAssignment.save();

        res.json({
            recommendedLaptop: {
                serialNumber: laptop.serialNumber,
                model: laptop.model,
                brand: laptop.brand,
                specifications: laptop.specifications
            }
        });
    } catch (error) {
        console.error('Error in /api/recommendations:', error);
        res.status(500).json({ error: 'An internal error occurred' });
    }
});

app.post('/api/reserve', async (req, res) => {
    try {
        const { name, laptopId } = req.body;
        if (!name || !laptopId) return res.status(400).json({ error: 'Employee name and laptop ID are required' });

        const employee = await Employee.findOne({ name });
        if (!employee) return res.status(404).json({ error: 'Employee not found' });

        const laptop = await Laptop.findById(laptopId);
        if (!laptop) return res.status(404).json({ error: 'Laptop not found' });

        if (laptop.status !== 'Available') return res.status(400).json({ error: 'Laptop is not available' });

        const reservation = new Reservation({
            employeeId: employee._id,
            laptopId: laptop._id,
            reservedDate: new Date(),
            status: 'Reserved'
        });
        await reservation.save();

        await Laptop.updateOne({ _id: laptop._id }, { status: 'Reserved' });

        res.json({ message: 'Laptop reserved successfully' });
    } catch (error) {
        console.error('Error in /api/reserve:', error);
        res.status(500).json({ error: 'An internal error occurred' });
    }
});

// Start the server
const port = process.env.PORT || 3000;
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
