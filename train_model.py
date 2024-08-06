import pandas as pd
import pickle
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LinearRegression
from bson import ObjectId
from config import get_db
import numpy as np
# Connect to MongoDB
db = get_db()

# Fetch data from MongoDB
assignments = list(db.Assignments.find({"status": "Active"}))
employees = list(db.Employees.find())
laptops = list(db.Laptops.find())

# Convert to DataFrames
assignment_df = pd.DataFrame(assignments)
employee_df = pd.DataFrame(employees)
laptop_df = pd.DataFrame(laptops)

# Flatten the specifications dictionary in laptop_df
specs_df = laptop_df['specifications'].apply(pd.Series)
laptop_df = pd.concat([laptop_df.drop(columns=['specifications']), specs_df], axis=1)

# Merge DataFrames
assignment_df['employeeId'] = assignment_df['employeeId'].astype(str)
employee_df['_id'] = employee_df['_id'].astype(str)

merged_df = assignment_df.merge(employee_df, left_on='employeeId', right_on='_id')

# Add laptop details to the merged DataFrame
laptop_df['_id'] = laptop_df['_id'].astype(str)
merged_df = merged_df.merge(laptop_df, left_on='laptopId', right_on='_id', suffixes=('_employee', '_laptop'))

# Prepare the data for training
X = merged_df[['cpu', 'ram', 'storage']]  # Ensure the features are correct
y = merged_df['laptopId']

# Encode categorical data
label_encoders = {}
for column in X.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    X[column] = le.fit_transform(X[column])
    label_encoders[column] = le

# Encode the target variable
le_target = LabelEncoder()
y = le_target.fit_transform(y)

# Map integers back to ObjectIds
id_mapping = dict(zip(le_target.transform(le_target.classes_), le_target.classes_))

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = KNeighborsClassifier(n_neighbors=3)
model.fit(X_train, y_train)

# Save the model, label encoders, and id mapping
with open('laptop_recommendation_model.pkl', 'wb') as file:
    pickle.dump((model, label_encoders, id_mapping), file)

print("Model trained and saved successfully.")

# Load the model, label encoders, and id mapping
with open('laptop_recommendation_model.pkl', 'rb') as file:
    model, label_encoders, id_mapping = pickle.load(file)

# Function to recommend and assign a laptop for a new hire
def onboard_new_hire(new_employee):
    # Extract relevant details for prediction
    employee_details = {
        'cpu': new_employee['cpu'],
        'ram': new_employee['ram'],
        'storage': new_employee['storage']
    }
    
    # Encode the details
    for column, le in label_encoders.items():
        employee_details[column] = le.transform([employee_details[column]])[0]
    
    # Convert to DataFrame
    employee_df = pd.DataFrame([employee_details])
    
    # Predict the laptop
    predicted_laptop_idx = model.predict(employee_df)[0]
    predicted_laptop_id = id_mapping[predicted_laptop_idx]
    
    # Check the availability of the recommended laptop
    laptop = db.Laptops.find_one({"_id": ObjectId(predicted_laptop_id), "status": "Available"})
    
    if laptop:
        # Assign the laptop to the new hire
        db.Assignments.insert_one({
            "employeeId": new_employee['_id'],
            "laptopId": predicted_laptop_id,
            "status": "Active"
        })
        
        # Update the laptop status
        db.Laptops.update_one({"_id": ObjectId(predicted_laptop_id)}, {"$set": {"status": "Assigned"}})
        
        print(f"Laptop {predicted_laptop_id} assigned to employee {new_employee['_id']}.")
    else:
        print("No available laptops match the criteria for the new hire.")

# Function to track offboarding and return laptops
def offboard_employee(employee_id):
    # Find all active assignments for the employee
    active_assignments = db.Assignments.find({"employeeId": employee_id, "status": "Active"})
    
    for assignment in active_assignments:
        laptop_id = assignment['laptopId']
        
        # Mark the laptop as available
        db.Laptops.update_one({"_id": ObjectId(laptop_id)}, {"$set": {"status": "Available"}})
        
        # Update the assignment status to "Returned"
        db.Assignments.update_one({"_id": assignment['_id']}, {"$set": {"status": "Returned"}})
        
        print(f"Laptop {laptop_id} returned by employee {employee_id}.")
    
    # Optional: Notify relevant teams or log the offboarding process
    print(f"Offboarding process completed for employee {employee_id}.")

# Function to forecast laptop demand
def forecast_laptop_demand():
    # Fetch historical assignment data
    historical_data = list(db.Assignments.find({"status": "Active"}))
    historical_df = pd.DataFrame(historical_data)
    
    # Feature engineering for demand forecasting
    historical_df['assignedDate'] = pd.to_datetime(historical_df['assignedDate'])
    historical_df['month'] = historical_df['assignedDate'].dt.to_period('M')
    demand_df = historical_df.groupby(['month', 'laptopId']).size().reset_index(name='demand')
    
    # Pivot the data for modeling
    demand_pivot = demand_df.pivot(index='month', columns='laptopId', values='demand').fillna(0)
    
    # Train a Linear Regression model to forecast demand
    X_demand = np.arange(len(demand_pivot)).reshape(-1, 1)  # Time index
    y_demand = demand_pivot.values
    demand_model = LinearRegression()
    demand_model.fit(X_demand, y_demand)
    
    # Save the demand forecasting model
    with open('laptop_demand_model.pkl', 'wb') as file:
        pickle.dump(demand_model, file)
    
    print("Demand forecasting model trained and saved successfully.")

# Load the demand forecasting model
def load_demand_model():
    try:
        with open('laptop_demand_model.pkl', 'rb') as file:
            demand_model = pickle.load(file)
        return demand_model
    except Exception as e:
        print(f"Error loading demand forecasting model: {e}")
        return None

# Forecast demand for the upcoming period
def predict_laptop_demand(periods=12):
    demand_model = load_demand_model()
    if not demand_model:
        return {"error": "Demand forecasting model not available."}
    
    # Generate future periods
    future_periods = np.arange(len(demand_model.coef_[0]) + periods).reshape(-1, 1)
    
    # Predict future demand
    predicted_demand = demand_model.predict(future_periods)
    
    # Prepare results
    demand_forecast = {}
    for idx, laptop_id in enumerate(demand_model.coef_[0].keys()):
        demand_forecast[str(laptop_id)] = predicted_demand[:, idx].tolist()
    
    return demand_forecast

if __name__ == "__main__":
    forecast_laptop_demand()
