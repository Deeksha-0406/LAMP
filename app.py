from flask import Flask, request, jsonify
import pickle
import pandas as pd
from bson import ObjectId
from config import get_db
from datetime import datetime

app = Flask(__name__)

# Load the model and encoders
try:
    with open('laptop_recommendation_model.pkl', 'rb') as file:
        model, label_encoders = pickle.load(file)
except Exception as e:
    print(f"Error loading model and encoders: {e}")
    raise

# Connect to MongoDB
db = get_db()

@app.route('/api/recommendations', methods=['POST'])
def recommend_laptop():
    try:
        data = request.get_json()  # Use get_json() for JSON request
        employee_name = data.get('name')
        
        if not employee_name:
            return jsonify({"error": "Employee name is required"}), 400
        
        # Fetch employee details
        employee = db.Employees.find_one({"name": employee_name})
        if not employee:
            return jsonify({"error": "Employee not found"}), 404
        
        # Check for reserved laptops
        reservation = db.Reservations.find_one({"employeeId": str(employee["_id"]), "status": "Reserved"})
        if reservation:
            recommended_laptop = db.Laptops.find_one({"_id": ObjectId(reservation["laptopId"])})
            # Update reservation status to active
            db.Reservations.update_one({"_id": reservation["_id"]}, {"$set": {"status": "Active"}})
        else:
            # Prepare employee data for prediction
            laptop = db.Laptops.find_one({"status": "Available"})
            if not laptop:
                return jsonify({"error": "No available laptop found"}), 404
            
            employee_features = {
                'role': employee.get('role', ''),
                'experienceLevel': employee.get('experienceLevel', ''),
                'age': employee.get('age', 0),
                'cpu': laptop['specifications'].get('cpu', ''),
                'ram': laptop['specifications'].get('ram', ''),
                'storage': laptop['specifications'].get('storage', ''),
                'graphics': laptop['specifications'].get('graphics', '')
            }
            
            # Convert employee_features to DataFrame
            employee_df = pd.DataFrame([employee_features])
            
            # Encode categorical data
            for column in employee_df.select_dtypes(include=['object']).columns:
                if column in label_encoders:
                    employee_df[column] = label_encoders[column].transform(employee_df[column])
                else:
                    employee_df[column] = employee_df[column].astype(str)
            
            # Predict the best laptop
            prediction = model.predict(employee_df)[0]
            recommended_laptop = db.Laptops.find_one({"_id": ObjectId(prediction)})
        
        if not recommended_laptop:
            return jsonify({"error": "No laptop found for the recommendation"}), 404
        
        # Update laptop status
        db.Laptops.update_one(
            {"_id": recommended_laptop["_id"]},
            {"$set": {"status": "Assigned"}}
        )
        
        # Create a new assignment entry
        new_assignment = {
            "employeeId": str(employee["_id"]),
            "laptopId": str(recommended_laptop["_id"]),
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
    
    except Exception as e:
        print(f"Error in /api/recommendations: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

@app.route('/api/reserve', methods=['POST'])
def reserve_laptop():
    try:
        data = request.get_json()  # Use get_json() for JSON request
        employee_name = data.get('name')
        laptop_id = data.get('laptopId')
        
        if not employee_name or not laptop_id:
            return jsonify({"error": "Employee name and laptop ID are required"}), 400
        
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
            "employeeId": str(employee["_id"]),
            "laptopId": str(laptop["_id"]),
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
    
    except Exception as e:
        print(f"Error in /api/reserve: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

if __name__ == '__main__':
    app.run(debug=True)
