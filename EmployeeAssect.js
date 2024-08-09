import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import './EmployeeAssect.css';

function Modal({ message, onClose }) {
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <p>{message}</p>
        <button className="modal-close" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}

function EmployeeAssect() {
  const { name } = useParams();
  const [employee, setEmployee] = useState(null);
  const [formData, setFormData] = useState({
    asset: '',
    specification: '',
    otherDetails: ''
  });
  const [modalVisible, setModalVisible] = useState(false);
  const [modalMessage, setModalMessage] = useState('');

  useEffect(() => {
    const fetchEmployee = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/employees/${encodeURIComponent(name)}`);
        const data = await response.json();
        console.log('Fetched employee data:', data);
        setEmployee(data);
      } catch (error) {
        console.error('Error fetching employee data:', error);
      }
    };

    fetchEmployee();
  }, [name]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevState => ({ ...prevState, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const recommendationData = {
      cpu: formData.asset,
      ram: formData.specification,
      storage: formData.otherDetails
    };

    try {
      const response = await fetch('http://localhost:5000/api/recommendations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(recommendationData)
      });
      if (response.ok) {
        const result = await response.json();
        console.log('Form data submitted successfully:', recommendationData);
        setModalMessage(`Form submitted successfully! Response: ${JSON.stringify(result)}`);
      } else {
        setModalMessage('Failed to submit form data');
      }
      setModalVisible(true);
    } catch (error) {
      console.error('Error submitting form data:', error);
      setModalMessage('Error submitting form data');
      setModalVisible(true);
    }
  };

  const handleCancel = () => {
    setFormData({
      asset: '',
      specification: '',
      otherDetails: ''
    });
  };

  const handleCloseModal = () => {
    setModalVisible(false);
  };

  if (!employee) return <p>Loading...</p>;

  return (
    <div className="employee-assect">
      <h1 className="employee-name">{employee.name}</h1>
      <div className="employee-info">
        <p><strong>Employee ID:</strong> {employee.employee_id}</p>
        <p><strong>Role:</strong> {employee.role}</p>
        <p><strong>Experience Level:</strong> {employee.experienceLevel}</p>
        <p><strong>Date Joined:</strong> {employee.dateJoined}</p>
        <p><strong>Preferences:</strong> {employee.preferences}</p>
        <p><strong>Project Needs:</strong> {employee.projectNeeds}</p>
        <p><strong>Email:</strong> <a href={`mailto:${employee.email}`}>{employee.email}</a></p>
      </div>
      
      <form onSubmit={handleSubmit} className="employee-form">
        <div className="form-group">
          <label htmlFor="asset">CPU:</label>
          <input
            type="text"
            id="asset"
            name="asset"
            className="form-control"
            value={formData.asset}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="specification">RAM:</label>
          <input
            type="text"
            id="specification"
            name="specification"
            className="form-control"
            value={formData.specification}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="otherDetails">STORAGE:</label>
          <textarea
            id="otherDetails"
            name="otherDetails"
            className="form-control"
            value={formData.otherDetails}
            onChange={handleChange}
          ></textarea>
        </div>
        <div className="form-actions">
          <button type="submit" className="submit-button">Submit</button>
          <button type="button" className="cancel-button" onClick={handleCancel}>Cancel</button>
        </div>
      </form>

      {modalVisible && <Modal message={modalMessage} onClose={handleCloseModal} />}
    </div>
  );
}

export default EmployeeAssect;
