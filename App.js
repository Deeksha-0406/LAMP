import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';
import Header from './Components/Header';
import Form from './Components/form';
import HomePage from './Components/Homepage';
import EmployeeDetails from './Components/Employeedetails';
import EmployeeAssect from './Components/EmployeeAssect';
import AboutUs from './Components/AboutUs';
 
function App() {
  return (
    <Router>
      <div className="app">
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/add-employee" element={<Form />} />
            <Route path="/employee-details" element={<EmployeeDetails />} />
            <Route path="/employee/:name" element={<EmployeeAssect />} />
            <Route path="/about-us" element={<AboutUs />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
 
export default App;
 