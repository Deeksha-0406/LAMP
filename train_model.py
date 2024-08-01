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

# Fetch data from MongoDB with correct collection names
assignments = list(db.Assignments.find())
employees = list(db.Employees.find())
laptops = list(db.Laptops.find())

# Convert to DataFrames
assignment_df = pd.DataFrame(assignments)
employee_df = pd.DataFrame(employees)
laptop_df = pd.DataFrame(laptops)

# Flatten the nested 'specifications' field in laptop_df
if 'specifications' in laptop_df.columns:
    specs_df = pd.json_normalize(laptop_df['specifications'])
    laptop_df = pd.concat([laptop_df.drop(columns=['specifications']), specs_df], axis=1)

# Check DataFrame columns
print("Assignment DF Columns: ", assignment_df.columns)
print("Employee DF Columns: ", employee_df.columns)
print("Laptop DF Columns: ", laptop_df.columns)

# Handle empty DataFrames
if assignment_df.empty or employee_df.empty or laptop_df.empty:
    print("One or more DataFrames are empty. Please check your MongoDB data.")
    exit()

# Merge DataFrames
assignment_df['employeeId'] = assignment_df['employeeId'].astype(str)
employee_df['_id'] = employee_df['_id'].astype(str)

merged_df = assignment_df.merge(employee_df, left_on='employeeId', right_on='_id')

# Add laptop details to the merged DataFrame
laptop_df['_id'] = laptop_df['_id'].astype(str)
merged_df = merged_df.merge(laptop_df, left_on='laptopId', right_on='_id', suffixes=('_employee', '_laptop'))

# Prepare the data for training
features = ['role', 'experienceLevel', 'age', 'cpu', 'ram', 'storage', 'graphics']
X = merged_df[features]
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
