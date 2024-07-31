import pymongo
import pickle
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Connect to MongoDB
client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['LAMP']
laptops = db['Laptops']

# Load the model and encoders
with open('predict_maintenance_model.pkl', 'rb') as f:
    model = pickle.load(f)

# Initialize encoders
status_encoder = LabelEncoder()
location_encoder = LabelEncoder()

# Load data to initialize encoders
laptop_data = pd.DataFrame(list(laptops.find()))
status_encoder.fit(laptop_data['status'])
location_encoder.fit(laptop_data['location'])

def predict_maintenance():
    # Prepare input for prediction (Assuming we need to predict for all laptops)
    input_data = pd.DataFrame(list(laptops.find()))
    
    # Encode status and location
    input_data['status'] = status_encoder.transform(input_data['status'])
    input_data['location'] = location_encoder.transform(input_data['location'])
    
    # Predict maintenance needs
    predictions = model.predict(input_data)
    
    # Map predictions back to readable format (if needed)
    return predictions.tolist()

if __name__ == "__main__":
    result = predict_maintenance()
    print(result)
