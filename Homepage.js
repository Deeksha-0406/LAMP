import React from 'react';
import './Homepage.css';
 
const HomePage = () => {
  return (
    <div className="home-page">
      <header className="home-header">
        <h1>Welcome to Our Laptop Asset Management Platform </h1>
        <p>Your one-stop solution for managing laptops records efficiently.</p>
      </header>
      <div className="home-features">
        <div className="feature-card">
          <div className="icon-container">
            <i className="fa fa-user-plus fa-3x"></i>
          </div>
          <h2>Add Employee</h2>
          <p>Create and manage employee records easily.</p>
          <a href="/add-employee" className="btn">Add Now</a>
        </div>
        <div className="feature-card">
          <div className="icon-container">
            <i className="fa fa-info-circle fa-3x"></i>
          </div>
          <h2>View Employee Details</h2>
          <p>Access detailed information about employees.</p>
          <a href="/employee-details" className="btn">View Details</a>
        </div>
        <div className="feature-card">
          <div className="icon-container">
            <i className="fa fa-info fa-3x"></i>
          </div>
          <h2>About Us</h2>
          <p>Learn more about our company and mission.</p>
          <a href="/about-us" className="btn">Read More</a>
        </div>
      </div>
    </div>
  );
};
 
export default HomePage;
 