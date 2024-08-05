from flask import Flask, request, jsonify
import pickle
import pandas as pd
from bson import ObjectId
from config import get_db
from datetime import datetime
import numpy as np

app = Flask(__name__)

# Load the model and encoders
try:
    with open('laptop_recommendation_model.pkl', 'rb') as file:
        model, label_encoders, id_mapping = pickle.load(file)
except Exception as e:
    print(f"Error loading model and encoders: {e}")
    raise

# Connect to MongoDB
db = get_db()

@app.route('/api/recommendations', methods=['POST'])
def recommend_laptop():
    try:
        data = request.get_json()
        
        # Get laptop requirements from the request
        requirements = {
            'cpu': data.get('cpu', ''),
            'ram': data.get('ram', ''),
            'storage': data.get('storage', '')
        }
        
        # Convert requirements to DataFrame
        requirements_df = pd.DataFrame([requirements])
        
        # Replace empty strings with NaN
        requirements_df.replace('', np.nan, inplace=True)
        
        # Ensure that 'cpu', 'ram', and 'storage' are numeric
        requirements_df['cpu'] = pd.to_numeric(requirements_df['cpu'], errors='coerce')
        requirements_df['ram'] = pd.to_numeric(requirements_df['ram'], errors='coerce')
        requirements_df['storage'] = pd.to_numeric(requirements_df['storage'], errors='coerce')
        
        # Fill NaN with 0 or another appropriate value
        requirements_df.fillna(0, inplace=True)
        
        # Encode categorical data
        for column in requirements_df.columns:
            if column in label_encoders:
                le = label_encoders[column]
                requirements_df[column] = requirements_df[column].apply(lambda x: le.transform([x])[0] if pd.notna(x) and x in le.classes_ else -1)
        
        # Ensure all columns are of the correct type
        for column in requirements_df.columns:
            if column in label_encoders:
                requirements_df[column] = requirements_df[column].astype(int)
            else:
                requirements_df[column] = requirements_df[column].astype(float)
        
        # Predict the best laptop
        prediction = model.predict(requirements_df)[0]
        
        # Map prediction integer to ObjectId string
        laptop_id = id_mapping.get(prediction, None)
        if not laptop_id:
            return jsonify({"error": "No laptop found for the recommendation"}), 404
        
        # Ensure laptop_id is a valid ObjectId
        try:
            predicted_laptop_id = ObjectId(laptop_id)
        except Exception as e:
            return jsonify({"error": f"Invalid laptop ID format: {laptop_id}"}), 400
        
        # Fetch the recommended laptop from the database
        recommended_laptop = db.Laptops.find_one({"_id": predicted_laptop_id})
        
        if not recommended_laptop:
            return jsonify({"error": "No laptop found for the recommendation"}), 404
        
        # Update laptop status
        db.Laptops.update_one(
            {"_id": recommended_laptop["_id"]},
            {"$set": {"status": "Assigned"}}
        )
        
        # Create a new assignment entry
        new_assignment = {
            "employeeId": None,  # No employee associated for this request
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
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

@app.route('/api/reserve', methods=['POST'])
def reserve_laptop():
    try:
        data = request.get_json()
        employee_name = data.get('name')
        laptop_id = data.get('laptopId')
        
        if not employee_name or not laptop_id:
            return jsonify({"error": "Employee name and laptop ID are required"}), 400
        
        # Fetch employee details
        employee = db.Employees.find_one({"name": employee_name})
        if not employee:
            return jsonify({"error": "Employee not found"}), 404
        
        # Ensure laptop_id is a valid ObjectId
        try:
            laptop_id = ObjectId(laptop_id)
        except Exception as e:
            return jsonify({"error": f"Invalid laptop ID format: {laptop_id}"}), 400
        
        # Fetch laptop details
        laptop = db.Laptops.find_one({"_id": laptop_id})
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
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
