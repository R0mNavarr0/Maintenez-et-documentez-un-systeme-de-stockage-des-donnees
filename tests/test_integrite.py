import pandas as pd
from pymongo import MongoClient
import pytest
import kagglehub
import time
from pymongo.errors import ServerSelectionTimeoutError

@pytest.fixture(scope="module")
def dataframes():
    path = kagglehub.dataset_download("prasad22/healthcare-dataset")
    df_csv = pd.read_csv(path + "/healthcare_dataset.csv")

    df_csv['Name'] = df_csv['Name'].str.upper()
    df_csv['Date of Admission'] = pd.to_datetime(df_csv['Date of Admission'])
    df_csv['Discharge Date'] = pd.to_datetime(df_csv['Discharge Date'])

    client = MongoClient("mongodb://mongodb:27017", serverSelectionTimeoutMS=1000)
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
    db = client["base"]
    collection = db["ma_collection"]
    docs_mongo = list(collection.find())
    df_mongo = pd.DataFrame(docs_mongo).drop(columns=["_id"], errors="ignore")

    return df_csv, df_mongo

def test_nombre_enregistrements(dataframes):
    df_csv, df_mongo = dataframes
    assert len(df_csv) == len(df_mongo), "Nombre de lignes différent entre CSV et MongoDB"

def test_colonnes_identiques(dataframes):
    df_csv, df_mongo = dataframes
    assert set(df_csv.columns) == set(df_mongo.columns), "Colonnes différentes entre CSV et MongoDB"

def test_somme_colonnes_numeriques(dataframes):
    df_csv, df_mongo = dataframes
    col_num = df_csv.select_dtypes(include=['number']).columns

    for col in col_num:
        csv_num_sum = df_csv[col].sum()
        mongo_num_sum = df_mongo[col].sum()
        csv_num_mean = df_csv[col].mean()
        mongo_num_mean = df_mongo[col].mean()

        ecart_somme = abs(csv_num_sum - mongo_num_sum)
        ecart_moyenne = abs(csv_num_mean - mongo_num_mean)

        assert ecart_somme < 1e-5 and ecart_moyenne < 1e-5, \
            f"Écart détecté pour la colonne numérique '{col}' :\n" \
            f" Somme CSV = {csv_num_sum}, Mongo = {mongo_num_sum}\n" \
            f" Moyenne CSV = {csv_num_mean}, Mongo = {mongo_num_mean}"
