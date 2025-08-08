#Importation des packages
import pandas as pd
import kagglehub
from pymongo import MongoClient
import time
from pymongo.errors import ServerSelectionTimeoutError
import os

def migrer_vers_mongo(client=None):

    # 1. Télécharger et préparer les données
    path = kagglehub.dataset_download("prasad22/healthcare-dataset")

    try :
        df = pd.read_csv(path + '/healthcare_dataset.csv')
    except MemoryError:
        chuncks = []
        for chunck in pd.read_csv(path + "/healthcare_dataset.csv", chunksize=5000):
            chuncks.append(chunck)
        df = pd.concat(chuncks, ignore_index=True)

    df['Name'] = df['Name'].str.upper()
    df['Date of Admission'] = pd.to_datetime(df['Date of Admission'])
    df['Discharge Date'] = pd.to_datetime(df['Discharge Date'])

    # 2. Connexion Mongo
    username = os.environ["APP_WRITER_USER"]
    password = os.environ["APP_WRITER_PASSWORD"]
    db_name = os.environ["MONGO_DB_NAME"]

    if client is None:
        client = MongoClient(
            f"mongodb://{username}:{password}@mongodb:27017/?authSource={db_name}",
            serverSelectionTimeoutMS=5000,
            maxPoolSize=50,
            retryWrites=True
        )

    db = client["base"]

    collection = db["ma_collection"]

    data = df.to_dict(orient='records')

    collection.delete_many({})

    collection.insert_many(data)

if __name__ == "__main__":
    migrer_vers_mongo()