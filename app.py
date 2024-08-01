# app.py
from flask import Flask, request, jsonify
import pickle
import pandas as pd
from bson import ObjectId
from config import get_db
from datetime import datetime

app = Flask(__name__)

# Load the model and encoders
with open('laptop_recommendation_model.pkl', 'rb') as file:
    model, label_encoders = pickle.load(file)

# Connect to MongoDB
db = get_db()

@app.route('/api/recommendations', methods=['POST'])
def recommend_laptop():
    data = request.json
    employee_name = data.get('employeeName')
    
    # Fetch employee details
    employee = db.Employees.find_one({"name": employee_name})
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    
    # Check for reserved laptops
    reservation = db.Reservations.find_one({"employeeId": employee["_id"], "status": "Reserved"})
    if reservation:
        recommended_laptop = db.Laptops.find_one({"_id": ObjectId(reservation["laptopId"])})
        # Update reservation status to active
        db.Reservations.update_one({"_id": reservation["_id"]}, {"$set": {"status": "Active"}})
    else:
        # Prepare employee data for prediction
        employee_features = {
            'role': employee['role'],
            'experienceLevel': employee['experienceLevel'],
            'age': data.get('age'),  # Assuming age is provided in the request
            'specifications.cpu': data.get('cpu'),  # Assuming CPU is provided in the request
            'specifications.ram': data.get('ram'),  # Assuming RAM is provided in the request
            'specifications.storage': data.get('storage'),  # Assuming Storage is provided in the request
            'specifications.graphics': data.get('graphics')  # Assuming Graphics is provided in the request
        }
        
        employee_df = pd.DataFrame([employee_features])
        
        # Encode categorical data
        for column in employee_df.select_dtypes(include=['object']).columns:
            if column in label_encoders:
                employee_df[column] = label_encoders[column].transform(employee_df[column])
        
        # Predict the best laptop
        prediction = model.predict(employee_df)[0]
        recommended_laptop = db.Laptops.find_one({"_id": ObjectId(prediction)})
    
    # Update laptop status
    db.Laptops.update_one(
        {"_id": recommended_laptop["_id"]},
        {"$set": {"status": "Assigned"}}
    )
    
    # Create a new assignment entry
    new_assignment = {
        "employeeId": employee["_id"],
        "laptopId": recommended_laptop["_id"],
        "assignedDate": datetime.utcnow(),
        "returnedDate": None,
        "status": "Active"
    }
    db.Assignments.insert_one(new_assignment)
    
    return jsonify({
        "recommendedLaptop": {
            "serialNumber": recommended_laptop['serialNumber'],
            "model": recommended_laptop['model'],
            "brand": recommended_laptop['brand'],
            "specifications": recommended_laptop['specifications']
        }
    })

@app.route('/api/reserve', methods=['POST'])
def reserve_laptop():
    data = request.json
    employee_name = data.get('employeeName')
    laptop_id = data.get('laptopId')
    
    # Fetch employee details
    employee = db.Employees.find_one({"name": employee_name})
    if not employee:
        return jsonify({"error": "Employee not found"}), 404
    
    # Fetch laptop details
    laptop = db.Laptops.find_one({"_id": ObjectId(laptop_id)})
    if not laptop:
        return jsonify({"error": "Laptop not found"}), 404
    
    # Check if the laptop is already reserved or assigned
    if laptop["status"] != "Available":
        return jsonify({"error": "Laptop is not available"}), 400
    
    # Create a new reservation entry
    new_reservation = {
        "employeeId": employee["_id"],
        "laptopId": laptop["_id"],
        "reservedDate": datetime.utcnow(),
        "status": "Reserved"
    }
    db.Reservations.insert_one(new_reservation)
    
    # Update laptop status to reserved
    db.Laptops.update_one(
        {"_id": laptop["_id"]},
        {"$set": {"status": "Reserved"}}
    )
    
    return jsonify({"message": "Laptop reserved successfully"})

if __name__ == '__main__':
    app.run(debug=True)
