from flask import Flask, request, jsonify
from pymongo import MongoClient
import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['LAMP']

# Load models and encoders
with open('smart_assignment_model.pkl', 'rb') as f:
    smart_assignment_model = pickle.load(f)
with open('predictive_maintenance_model.pkl', 'rb') as f:
    predictive_maintenance_model = pickle.load(f)

# Initialize encoders
role_encoder = LabelEncoder()
status_encoder = LabelEncoder()
location_encoder = LabelEncoder()
model_encoder = LabelEncoder()

# Initialize encoders with existing data
employees = pd.DataFrame(list(db.Employees.find()))
laptops = pd.DataFrame(list(db.Laptops.find()))

# Fit encoders with the data from MongoDB
role_encoder.fit(employees['role'])
status_encoder.fit(laptops['status'])
location_encoder.fit(laptops['location'])
model_encoder.fit(laptops['model'])

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/recommend_laptop', methods=['POST'])
def recommend_laptop():
    data = request.json
    employee_name = data.get('name')

    if not employee_name:
        return jsonify({'error': 'Missing employee name'}), 400

    # Fetch employee details
    employee = db.Employees.find_one({'name': employee_name})
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404

    # Encode employee role
    try:
        employee_role = role_encoder.transform([employee['role']])[0]
    except ValueError:
        return jsonify({'error': 'Invalid employee role'}), 400

    # Predict laptop model
    X = pd.DataFrame([[employee_role, 0, 0]], columns=['role', 'status', 'location'])
    recommended_model_code = smart_assignment_model.predict(X)[0]
    recommended_model = model_encoder.inverse_transform([recommended_model_code])[0]

    # Check laptop availability
    available_laptop = db.Laptops.find_one({'model': recommended_model, 'status': 'available'})
    if available_laptop:
        # Update laptop status
        db.Laptops.update_one(
            {'_id': available_laptop['_id']},
            {'$set': {'assignedTo': employee_name, 'status': 'assigned'}}
        )
        return jsonify({
            'message': f'Laptop {available_laptop["model"]} assigned to {employee_name}',
            'laptop': available_laptop
        }), 200
    else:
        return jsonify({'message': 'No available laptops for the recommended model'}), 200

@app.route('/api/reserve_laptop', methods=['POST'])
def reserve_laptop():
    data = request.json
    manager_name = data.get('manager_name')
    employee_name = data.get('employee_name')
    model = data.get('model')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not all([manager_name, employee_name, model, start_date, end_date]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # Check laptop availability for reservation period
    reserved_laptop = db.Laptops.find_one({'model': model, 'status': 'available'})
    if reserved_laptop:
        # Update laptop status to reserved
        db.Laptops.update_one(
            {'_id': reserved_laptop['_id']},
            {'$set': {'status': 'reserved', 'assignedTo': employee_name, 'reservationStartDate': start_date, 'reservationEndDate': end_date}}
        )
        return jsonify({'message': f'Laptop {reserved_laptop["model"]} reserved for {employee_name} by {manager_name}'}), 200
    else:
        return jsonify({'message': 'No available laptops for reservation'}), 200

@app.route('/api/predict_maintenance', methods=['GET'])
def predict_maintenance():
    laptops = pd.DataFrame(list(db.Laptops.find()))
    laptops['lastServiced'] = pd.to_datetime(laptops['lastServiced'])
    laptops['usage_duration'] = (datetime.now() - laptops['lastServiced']).dt.days

    X = laptops[['usage_duration', 'status', 'location']]
    X['status'] = status_encoder.transform(X['status'])
    X['location'] = location_encoder.transform(X['location'])

    maintenance_predictions = predictive_maintenance_model.predict(X)
    laptops['predicted_maintenance'] = maintenance_predictions

    # Recommend laptops for maintenance
    laptops_due_for_maintenance = laptops[laptops['predicted_maintenance'] > 180]  # threshold in days
    return laptops_due_for_maintenance.to_json(orient='records'), 200

@app.route('/api/onboard_employee', methods=['POST'])
def onboard_employee():
    data = request.json
    name = data.get('name')
    role = data.get('role')
    email = data.get('email')
    date_joined = data.get('dateJoined')

    if not all([name, role, email, date_joined]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Add new employee to the database
    db.Employees.insert_one({
        'name': name,
        'role': role,
        'email': email,
        'dateJoined': date_joined
    })

    return jsonify({'message': f'Employee {name} onboarded successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)
