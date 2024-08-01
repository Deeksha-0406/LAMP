# train_model.py
import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from bson import ObjectId
from config import get_db

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

# Check DataFrame columns
print("Assignment DF Columns: ", assignment_df.columns)
print("Employee DF Columns: ", employee_df.columns)
print("Laptop DF Columns: ", laptop_df.columns)

# Check for empty DataFrames
if assignment_df.empty:
    print("Assignment DataFrame is empty.")
if employee_df.empty:
    print("Employee DataFrame is empty.")
if laptop_df.empty:
    print("Laptop DataFrame is empty.")

# Stop execution if any DataFrame is empty
if assignment_df.empty or employee_df.empty or laptop_df.empty:
    raise ValueError("DataFrames are empty. Please check your MongoDB data.")

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
X = merged_df[['role', 'experienceLevel', 'age', 'cpu', 'ram', 'storage', 'graphics']]
y = merged_df['laptopId']

# Encode categorical data
label_encoders = {}
for column in X.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    X[column] = le.fit_transform(X[column])
    label_encoders[column] = le

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save the model and label encoders
with open('laptop_recommendation_model.pkl', 'wb') as file:
    pickle.dump((model, label_encoders), file)

print("Model trained and saved successfully.")
