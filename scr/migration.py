#Importation des packages
import pandas as pd
import kagglehub
from pymongo import MongoClient
import time
from pymongo.errors import ServerSelectionTimeoutError
import os

#Téléchargement du fichier CSV depuis l'API Kaggle
path = kagglehub.dataset_download("prasad22/healthcare-dataset")

df = pd.read_csv(path+'/healthcare_dataset.csv')

#Transformation des données
df['Name'] = df['Name'].str.upper()

df['Date of Admission'] =  pd.to_datetime(df['Date of Admission'])
df['Discharge Date'] =  pd.to_datetime(df['Discharge Date'])

#Système d'authentification avec ID et MDP
username = os.environ["APP_WRITER_USER"]
password = os.environ["APP_WRITER_PASSWORD"]
db_name = os.environ["MONGO_DB_NAME"]

#Connection à l'instance MongoDB
client = MongoClient(f"mongodb://{username}:{password}@mongodb:27017/?authSource={db_name}",serverSelectionTimeoutMS=5000)

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

#Création de la base de données
db = client['base']

#Création de la collection
collection = db['ma_collection']

#Transformation du DataFrame Pandas en un dictionnaire pour insertion dans MongoDB
data = df.to_dict(orient='records')

#Insertion des données dans MongoDB
collection.insert_many(data)