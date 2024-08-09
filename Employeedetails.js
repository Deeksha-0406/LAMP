import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Employeedetails.css';

const EmployeeDetails = () => {
  const [employees, setEmployees] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch employee data from the API
    const fetchEmployees = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/employees');
        const data = await response.json();
        setEmployees(data);
      } catch (error) {
        console.error('Error fetching employee data:', error);
      }
    };

    fetchEmployees();
  }, []);

  const handleCardClick = (name) => {
    navigate(`/employee/${encodeURIComponent(name)}`);
  };

  return (
    <div className="employee-details">
      {employees.length > 0 ? (
        employees.map((employee) => (
          <div
            key={employee._id}
            className="details-card"
            onClick={() => handleCardClick(employee.name)}
          >
            <div className="employee-info">
              <div className="info-item">
                <i className="fa fa-user fa-3x"></i>
                <div className="info-text">
                  <h2>{employee.name}</h2>
                  <p><strong>Position:</strong> {employee.position}</p>
                  <p><strong>Department:</strong> {employee.department}</p>
                </div>
              </div>
              <div className="info-item">
                <i className="fa fa-envelope fa-3x"></i>
                <div className="info-text">
                  <p><strong>Email:</strong> <a href={`mailto:${employee.email}`}>{employee.email}</a></p>
                </div>
              </div>
              <div className="info-item">
                <i className="fa fa-phone fa-3x"></i>
                <div className="info-text">
                  <p><strong>Phone:</strong> {employee.phone}</p>
                </div>
              </div>
            </div>
          </div>
        ))
      ) : (
        <p>Loading...</p>
      )}
    </div>
  );
};

export default EmployeeDetails;
