import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Header.css';

function Header() {
  const navigate = useNavigate();

  return (
    <div className="header">
      <h1>Laptop Asset Management Platform</h1>
      <div className="nav-links">
        <button className="nav-button" onClick={() => navigate('/')}>Home</button>
        <button className="nav-button" onClick={() => navigate('/add-employee')}>Add Employee</button>
        <button className="nav-button" onClick={() => navigate('/employee-details')}>Employee Details</button>
        <button className="nav-button" onClick={() => navigate('/about-us')}>About Us</button>
      </div>
    </div>
  );
}

export default Header;
