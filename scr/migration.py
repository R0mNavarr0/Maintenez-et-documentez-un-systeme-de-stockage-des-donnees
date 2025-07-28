import pandas as pd
import kagglehub
from pymongo import MongoClient
import time
from pymongo.errors import ServerSelectionTimeoutError
import os

path = kagglehub.dataset_download("prasad22/healthcare-dataset")

df = pd.read_csv(path+'/healthcare_dataset.csv')

df['Name'] = df['Name'].str.upper()

df['Date of Admission'] =  pd.to_datetime(df['Date of Admission'])
df['Discharge Date'] =  pd.to_datetime(df['Discharge Date'])

username = os.getenv("MONGO_INITDB_ROOT_USERNAME")
password = os.getenv("MONGO_INITDB_ROOT_PASSWORD")

client = MongoClient(f"mongodb://{username}:{password}@mongodb:27017/?authSource=admin",serverSelectionTimeoutMS=1000)

# Attente active jusqu'à ce que MongoDB soit prêt
for _ in range(30):  # max ~30s
    try:
        client.admin.command('ping')
        print("MongoDB est prêt !")
        break
    except ServerSelectionTimeoutError:
        print("En attente de MongoDB...")
        time.sleep(1)
else:
    print("MongoDB ne répond pas, abandon.")
    exit(1)

db = client['base']
collection = db['ma_collection']

data = df.to_dict(orient='records')

collection.insert_many(data)