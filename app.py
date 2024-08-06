from flask import Flask, request, jsonify
import pickle
import pandas as pd
from bson import ObjectId
from config import get_db
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load the model and encoders
try:
    with open('laptop_recommendation_model.pkl', 'rb') as file:
        model, label_encoders, id_mapping = pickle.load(file)
except Exception as e:
    logging.error(f"Error loading model and encoders: {e}")
    raise

# Load the demand forecasting model
def load_demand_model():
    try:
        with open('laptop_demand_model.pkl', 'rb') as file:
            demand_model = pickle.load(file)
        return demand_model
    except Exception as e:
        logging.error(f"Error loading demand forecasting model: {e}")
        return None

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
        result = db.Laptops.update_one(
            {"_id": recommended_laptop["_id"]},
            {"$set": {"status": "Assigned"}}
        )
        if result.modified_count == 0:
            logging.warning(f"Laptop with ID {predicted_laptop_id} was not updated.")
        
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
        logging.error(f"Error in /api/recommendations: {e}")
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
        result = db.Reservations.insert_one(new_reservation)
        if result.inserted_id is None:
            logging.warning("Reservation entry was not created.")
        
        # Update laptop status to reserved
        result = db.Laptops.update_one(
            {"_id": laptop["_id"]},
            {"$set": {"status": "Reserved"}}
        )
        if result.modified_count == 0:
            logging.warning(f"Laptop with ID {laptop_id} was not updated.")
        
        return jsonify({"message": "Laptop reserved successfully"})
    
    except Exception as e:
        logging.error(f"Error in /api/reserve: {e}")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

@app.route('/api/onboard', methods=['POST'])
def onboard_new_hire():
    try:
        data = request.get_json()
        new_employee = {
            '_id': data.get('_id'),
            'cpu': data.get('cpu'),
            'ram': data.get('ram'),
            'storage': data.get('storage')
        }
        
        if not new_employee['_id'] or not new_employee['cpu'] or not new_employee['ram'] or not new_employee['storage']:
            return jsonify({"error": "Employee ID, cpu, ram, and storage are required"}), 400
        
        # Extract relevant details for prediction
        employee_details = {
            'cpu': new_employee['cpu'],
            'ram': new_employee['ram'],
            'storage': new_employee['storage']
        }
        
        # Convert to DataFrame
        employee_df = pd.DataFrame([employee_details])
        
        # Encode the details
        for column, le in label_encoders.items():
            if column in employee_df.columns:
                employee_df[column] = employee_df[column].apply(lambda x: le.transform([x])[0] if pd.notna(x) and x in le.classes_ else -1)
        
        # Ensure all columns are of the correct type
        for column in employee_df.columns:
            if column in label_encoders:
                employee_df[column] = employee_df[column].astype(int)
            else:
                employee_df[column] = employee_df[column].astype(float)
        
        # Predict the laptop
        predicted_laptop_idx = model.predict(employee_df)[0]
        predicted_laptop_id = id_mapping[predicted_laptop_idx]
        
        # Debugging information
        logging.debug(f"Predicted laptop index: {predicted_laptop_idx}")
        logging.debug(f"Predicted laptop ID: {predicted_laptop_id}")
        
        # Ensure laptop_id is a valid ObjectId
        try:
            predicted_laptop_id = ObjectId(predicted_laptop_id)
        except Exception as e:
            return jsonify({"error": f"Invalid laptop ID format: {predicted_laptop_id}"}), 400
        
        # Check the availability of the recommended laptop
        laptop = db.Laptops.find_one({"_id": predicted_laptop_id, "status": "Available"})
        
        # Debugging information
        logging.debug(f"Laptop found: {laptop}")
        
        if laptop:
            # Assign the laptop to the new hire
            result = db.Assignments.insert_one({
                "employeeId": new_employee['_id'],
                "laptopId": str(predicted_laptop_id),
                "status": "Active",
                "assignedDate": datetime.utcnow()
            })
            if result.inserted_id is None:
                logging.warning("Assignment entry was not created.")
            
            # Update the laptop status
            result = db.Laptops.update_one({"_id": predicted_laptop_id}, {"$set": {"status": "Assigned"}})
            if result.modified_count == 0:
                logging.warning(f"Laptop with ID {predicted_laptop_id} was not updated.")
            
            return jsonify({
                "message": f"Laptop {predicted_laptop_id} assigned to employee {new_employee['_id']}.",
                "laptop": {
                    "serialNumber": laptop['serialNumber'],
                    "model": laptop['model'],
                    "brand": laptop['brand'],
                    "specifications": laptop['specifications']
                }
            })
        else:
            return jsonify({"error": "No available laptops match the criteria for the new hire."}), 404
    
    except Exception as e:
        logging.error(f"Error in /api/onboard: {e}")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

@app.route('/api/offboard', methods=['POST'])
def offboard_employee():
    try:
        data = request.get_json()
        employee_id = data.get('employeeId')
        
        if not employee_id:
            return jsonify({"error": "Employee ID is required"}), 400
        
        # Find all active assignments for the employee
        active_assignments = list(db.Assignments.find({"employeeId": employee_id, "status": "Active"}))
        if not active_assignments:
            return jsonify({"message": "No active assignments found for this employee"}), 404
        
        for assignment in active_assignments:
            try:
                laptop_id = ObjectId(assignment['laptopId'])
                laptop = db.Laptops.find_one({"_id": laptop_id})
                
                if not laptop:
                    logging.warning(f"Laptop with ID {laptop_id} not found.")
                    continue
                
                result = db.Assignments.update_one(
                    {"_id": assignment["_id"]},
                    {"$set": {"returnedDate": datetime.utcnow(), "status": "Returned"}}
                )
                if result.matched_count == 0:
                    logging.warning(f"Assignment with ID {assignment['_id']} not found for update.")
                
                result = db.Laptops.update_one(
                    {"_id": laptop["_id"]},
                    {"$set": {"status": "Available"}}
                )
                if result.matched_count == 0:
                    logging.warning(f"Laptop with ID {laptop['_id']} not found for update.")
            
            except Exception as e:
                logging.error(f"Error updating assignment or laptop: {e}")
        
        return jsonify({"message": "Employee offboarding processed successfully"})
    
    except Exception as e:
        logging.error(f"Error in /api/offboard: {e}")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

@app.route('/api/forecast_demand', methods=['GET'])
def forecast_laptop_demand():
    try:
        demand_model = load_demand_model()
        if not demand_model:
            return jsonify({"error": "Demand forecasting model not available."}), 500
        
        # Generate future periods
        historical_data = list(db.Assignments.find({"status": "Active"}))
        historical_df = pd.DataFrame(historical_data)
        historical_df['assignedDate'] = pd.to_datetime(historical_df['assignedDate'])
        historical_df['month'] = historical_df['assignedDate'].dt.to_period('M')
        demand_df = historical_df.groupby(['month', 'laptopId']).size().reset_index(name='demand')
        demand_pivot = demand_df.pivot(index='month', columns='laptopId', values='demand').fillna(0)
        future_periods = np.arange(len(demand_pivot) + 12).reshape(-1, 1)  # Forecast for 12 periods ahead
        
        # Predict future demand
        predicted_demand = demand_model.predict(future_periods)
        
        # Prepare results
        demand_forecast = {}
        for idx, laptop_id in enumerate(demand_pivot.columns):
            demand_forecast[str(laptop_id)] = predicted_demand[:, idx].tolist()
        
        return jsonify({"demandForecast": demand_forecast})
    
    except Exception as e:
        logging.error(f"Error in /api/forecast_demand: {e}")
        return jsonify({"error": f"An internal error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
