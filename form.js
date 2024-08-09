import React from 'react';
import './form.css';

function Form() {
  return (
    <div className="form-container">
      <form>
        <div className="form-group">
          <label htmlFor="employeeName">Employee Name:</label>
          <input type="text" id="employeeName" name="employeeName" />
        </div>
        <div className="form-group">
          <label htmlFor="employeeId">Employee ID:</label>
          <input type="text" id="employeeId" name="employeeId" />
        </div>
        <div className="form-group">
          <label htmlFor="employeeId">Role:</label>
          <input type="text" id="employeeId" name="employeeId" />
        </div>
        <div className="form-group">
          <label htmlFor="employeeId">Email:</label>
          <input type="text" id="employeeId" name="employeeId" />
        </div>
        <div className="form-group">
          <label htmlFor="preference">Preference:</label>
          <select id="preference" name="preference">
            <option value="option1">Option 1</option>
            <option value="option2">Option 2</option>
            <option value="option3">Option 3</option>
          </select>
        </div>
        <div className="form-group">
          <label htmlFor="startDate">Date Joined</label>
          <input type="date" id="startDate" name="startDate" />
        </div>
        <div className="form-group">
          <label htmlFor="description">Description:</label>
          <textarea id="description" name="description"></textarea>
        </div>
      </form>
    </div>
  );
}

export default Form;
