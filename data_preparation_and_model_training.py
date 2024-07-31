import pandas as pd
from pymongo import MongoClient
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['LAMP']

# Load employee and laptop data
employees = pd.DataFrame(list(db.Employees.find()))
laptops = pd.DataFrame(list(db.Laptops.find()))

# Data Preparation
employees['dateJoined'] = pd.to_datetime(employees['dateJoined'])
laptops['lastServiced'] = pd.to_datetime(laptops['lastServiced'])

# Ensure lastServiced is timezone-naive
laptops['lastServiced'] = laptops['lastServiced'].dt.tz_localize(None)

# Fill NaN values
employees['role'].fillna('Unknown', inplace=True)
laptops['status'].fillna('unknown', inplace=True)
laptops['location'].fillna('unknown', inplace=True)

# Label encoding
role_encoder = LabelEncoder()
status_encoder = LabelEncoder()
location_encoder = LabelEncoder()
model_encoder = LabelEncoder()

employees['role_encoded'] = role_encoder.fit_transform(employees['role'])
laptops['status_encoded'] = status_encoder.fit_transform(laptops['status'])
laptops['location_encoded'] = location_encoder.fit_transform(laptops['location'])
laptops['model_encoded'] = model_encoder.fit_transform(laptops['model'])

# Merge data for Smart Assignment model
merged_data = employees.merge(laptops, left_on='name', right_on='assignedTo', how='left')

# Fill NaN values after merge
merged_data['status_encoded'].fillna(laptops['status_encoded'].mode()[0], inplace=True)
merged_data['location_encoded'].fillna(laptops['location_encoded'].mode()[0], inplace=True)
merged_data['model_encoded'].fillna(-1, inplace=True)  # Fill with -1 as a placeholder

# Prepare data for Smart Assignment model
X_assignment = merged_data[['role_encoded', 'status_encoded', 'location_encoded']]
y_assignment = merged_data['model_encoded']
X_train_assignment, X_test_assignment, y_train_assignment, y_test_assignment = train_test_split(X_assignment, y_assignment, test_size=0.2, random_state=42)

# Train Smart Assignment model
smart_assignment_model = RandomForestClassifier()
smart_assignment_model.fit(X_train_assignment, y_train_assignment)

# Save Smart Assignment model
with open('smart_assignment_model.pkl', 'wb') as f:
    pickle.dump(smart_assignment_model, f)

# Prepare data for Predictive Maintenance model
laptops['usage_duration'] = (pd.Timestamp.now() - laptops['lastServiced']).dt.days

# Prepare features and target for Predictive Maintenance
X_maintenance = laptops[['usage_duration', 'status_encoded', 'location_encoded']]
y_maintenance = laptops['usage_duration']  # This might need to be adjusted

# Train Predictive Maintenance model
X_train_maintenance, X_test_maintenance, y_train_maintenance, y_test_maintenance = train_test_split(X_maintenance, y_maintenance, test_size=0.2, random_state=42)
predictive_maintenance_model = RandomForestRegressor()
predictive_maintenance_model.fit(X_train_maintenance, y_train_maintenance)

# Save Predictive Maintenance model
with open('predictive_maintenance_model.pkl', 'wb') as f:
    pickle.dump(predictive_maintenance_model, f)

print("Models have been trained and saved successfully.")


#6
