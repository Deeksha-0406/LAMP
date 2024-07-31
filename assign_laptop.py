import sys
import pymongo
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Connect to MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['LAMP']
employees = db['Employees']
laptops = db['Laptops']

# Load the model and encoders
with open('smart_assignment_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Initialize encoders
role_encoder = LabelEncoder()
status_encoder = LabelEncoder()
location_encoder = LabelEncoder()
model_encoder = LabelEncoder()

# Load data to initialize encoders
employee_data = pd.DataFrame(list(employees.find()))
laptop_data = pd.DataFrame(list(laptops.find()))
role_encoder.fit(employee_data['role'])
status_encoder.fit(laptop_data['status'])
location_encoder.fit(laptop_data['location'])
model_encoder.fit(laptop_data['model'])

def assign_laptop(employee_name):
    print(f"Assigning laptop to employee: {employee_name}")  # Debugging line
    # Fetch employee details
    employee = employees.find_one({'name': employee_name})
    if not employee:
        return "Employee not found."

    employee_role = employee['role']
    
    # Prepare input for prediction
    input_data = pd.DataFrame([{
        'role': employee_role,
        'status': 'available',  # Assuming default values for status and location
        'location': 'Office'
    }])
    
    # Encode role, status, and location
    input_data['role'] = role_encoder.transform(input_data['role'])
    input_data['status'] = status_encoder.transform(input_data['status'])
    input_data['location'] = location_encoder.transform(input_data['location'])
    
    # Predict laptop model
    predicted_model_code = model.predict(input_data)[0]
    predicted_model = model_encoder.inverse_transform([predicted_model_code])[0]

    # Find available laptop
    laptop = laptops.find_one({'model': predicted_model, 'status': 'available'})
    if not laptop:
        return "No available laptop for the predicted model."

    # Assign laptop to employee
    laptops.update_one({'_id': laptop['_id']}, {'$set': {'assignedTo': employee_name, 'status': 'assigned'}})
    return f"Laptop {laptop['serialNumber']} assigned to {employee_name}."

if __name__ == "__main__":
    if len(sys.argv) > 1:
        employee_name = sys.argv[1]
        result = assign_laptop(employee_name)
        print(result)
    else:
        print("Employee name argument is required.")
