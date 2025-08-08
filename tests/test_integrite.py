# Importation des packages nécessaires
import pandas as pd
from pymongo import MongoClient
import pytest
import kagglehub
import time
from pymongo.errors import ServerSelectionTimeoutError
import os
import sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scr.migration import migrer_vers_mongo

class OptimizedDataFrameLoader:
    """Classe pour optimiser le chargement et la comparaison des données"""
    
    def __init__(self):
        self.df_csv = None
        self.mongo_stats = None
        self.client = None
        self.collection = None
        
    def setup_mongodb_connection(self):
        """Configuration optimisée de la connexion MongoDB"""
        username = os.environ["APP_WRITER_USER"]
        password = os.environ["APP_WRITER_PASSWORD"]
        db_name = os.environ["MONGO_DB_NAME"]
        
        self.client = MongoClient(
            f"mongodb://{username}:{password}@mongodb:27017/?authSource={db_name}",
            serverSelectionTimeoutMS=5000,
            # Optimisations de performance
            maxPoolSize=50,
            readPreference='secondaryPreferred',
            retryWrites=True
        )
        
        db = self.client["base"]
        self.collection = db["ma_collection"]
        
    def load_csv_data(self):
        """Chargement optimisé des données CSV"""
        if self.df_csv is not None:
            return self.df_csv
            
        path = kagglehub.dataset_download("prasad22/healthcare-dataset")
        
        # Lecture par chunks pour économiser la mémoire si le fichier est gros
        try:
            # Tentative de lecture normale d'abord 
            self.df_csv = pd.read_csv(path + "/healthcare_dataset.csv")
        except MemoryError:
            # Si trop gros, lecture par chunks
            logger.info("Lecture par chunks du fichier CSV...")
            chunks = []
            for chunk in pd.read_csv(path + "/healthcare_dataset.csv", chunksize=5000):
                chunks.append(chunk)
            self.df_csv = pd.concat(chunks, ignore_index=True)
        
        # Nettoyage des données (identique à migration.py)
        self.df_csv['Name'] = self.df_csv['Name'].str.upper()
        self.df_csv['Date of Admission'] = pd.to_datetime(self.df_csv['Date of Admission'])
        self.df_csv['Discharge Date'] = pd.to_datetime(self.df_csv['Discharge Date'])
        
        return self.df_csv
    
    def get_mongodb_stats_aggregated(self):
        """Récupération optimisée des statistiques MongoDB via agrégation"""
        if self.mongo_stats is not None:
            return self.mongo_stats
            
        if self.collection is None:
            self.setup_mongodb_connection()
        
        # Pipeline d'agrégation pour obtenir toutes les stats en une fois
        numeric_columns = ['Age', 'Billing Amount', 'Room Number']
        
        # Construction du pipeline d'agrégation dynamique
        group_stage = {
            "_id": None,
            "count": {"$sum": 1}
        }
        
        # Ajout des stats numériques
        for col in numeric_columns:
            group_stage[f"sum_{col}"] = {"$sum": f"${col}"}
            group_stage[f"avg_{col}"] = {"$avg": f"${col}"}
        
        pipeline = [{"$group": group_stage}]
        
        try:
            result = list(self.collection.aggregate(pipeline))[0]
            
            # Récupération des colonnes (un seul document d'exemple)
            sample_doc = self.collection.find_one()
            columns = [col for col in sample_doc.keys() if col != '_id'] if sample_doc else []
            
            # Structuration des résultats
            self.mongo_stats = {
                'count': result['count'],
                'columns': columns,
                'numeric_stats': {}
            }
            
            for col in numeric_columns:
                if f"sum_{col}" in result:
                    self.mongo_stats['numeric_stats'][col] = {
                        'sum': result[f"sum_{col}"],
                        'mean': result[f"avg_{col}"]
                    }
            
            logger.info(f"Stats MongoDB récupérées: {self.mongo_stats['count']} documents")
            return self.mongo_stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'agrégation MongoDB: {e}")
            # Fallback sur la méthode classique si l'agrégation échoue
            return self.get_mongodb_stats_fallback()
    
    def get_mongodb_stats_fallback(self):
        """Méthode de fallback si l'agrégation échoue"""
        logger.info("Utilisation de la méthode de fallback pour MongoDB")
        df_mongo = pd.DataFrame(list(self.collection.find())).drop(columns=["_id"], errors="ignore")
        
        numeric_columns = df_mongo.select_dtypes(include=['number']).columns
        
        self.mongo_stats = {
            'count': len(df_mongo),
            'columns': list(df_mongo.columns),
            'numeric_stats': {}
        }
        
        for col in numeric_columns:
            self.mongo_stats['numeric_stats'][col] = {
                'sum': float(df_mongo[col].sum()),
                'mean': float(df_mongo[col].mean())
            }
        
        return self.mongo_stats
    
    def cleanup(self):
        """Nettoyage des ressources"""
        if self.client:
            self.client.close()

# Instance globale pour réutiliser les données
_loader = OptimizedDataFrameLoader()

@pytest.fixture(scope="module")
def dataframes():
    """Fixture optimisée pour le chargement des données"""
    # Appel de la migration (inchangé)
    migrer_vers_mongo()
    
    # Chargement optimisé des données
    df_csv = _loader.load_csv_data()
    mongo_stats = _loader.get_mongodb_stats_aggregated()
    
    yield df_csv, mongo_stats
    
    # Nettoyage après les tests
    _loader.cleanup()

def test_nombre_enregistrements(dataframes):
    """Test optimisé du nombre d'enregistrements"""
    df_csv, mongo_stats = dataframes
    
    csv_count = len(df_csv)
    mongo_count = mongo_stats['count']
    
    logger.info(f"Comparaison comptage: CSV={csv_count}, MongoDB={mongo_count}")
    
    assert csv_count == mongo_count, \
        f"Nombre de lignes différent: CSV={csv_count}, MongoDB={mongo_count}"

def test_colonnes_identiques(dataframes):
    """Test optimisé de la structure de données"""
    df_csv, mongo_stats = dataframes
    
    csv_columns = set(df_csv.columns)
    mongo_columns = set(mongo_stats['columns'])
    
    logger.info(f"Colonnes CSV: {csv_columns}")
    logger.info(f"Colonnes MongoDB: {mongo_columns}")
    
    # Vérifications détaillées pour un meilleur debugging
    missing_in_mongo = csv_columns - mongo_columns
    extra_in_mongo = mongo_columns - csv_columns
    
    if missing_in_mongo:
        logger.warning(f"Colonnes manquantes dans MongoDB: {missing_in_mongo}")
    if extra_in_mongo:
        logger.warning(f"Colonnes supplémentaires dans MongoDB: {extra_in_mongo}")
    
    assert csv_columns == mongo_columns, \
        f"Colonnes différentes:\n" \
        f"Manquantes dans MongoDB: {missing_in_mongo}\n" \
        f"Supplémentaires dans MongoDB: {extra_in_mongo}"

def test_somme_colonnes_numeriques_optimized(dataframes):
    """Test optimisé sur les colonnes numériques avec vectorisation"""
    df_csv, mongo_stats = dataframes
    
    # Sélection des colonnes numériques du CSV
    col_num = df_csv.select_dtypes(include=['number']).columns
    
    errors = []
    tolerance = 1e-5
    
    for col in col_num:
        if col in mongo_stats['numeric_stats']:
            # Calculs vectorisés pour CSV
            csv_values = df_csv[col].dropna().values  # Conversion en numpy array
            csv_sum = float(np.sum(csv_values))
            csv_mean = float(np.mean(csv_values))
            
            # Récupération des stats MongoDB précalculées
            mongo_sum = mongo_stats['numeric_stats'][col]['sum']
            mongo_mean = mongo_stats['numeric_stats'][col]['mean']
            
            # Calcul des écarts
            ecart_somme = abs(csv_sum - mongo_sum)
            ecart_moyenne = abs(csv_mean - mongo_mean)
            
            logger.info(f"Colonne {col}: CSV_sum={csv_sum:.6f}, Mongo_sum={mongo_sum:.6f}, "
                       f"CSV_mean={csv_mean:.6f}, Mongo_mean={mongo_mean:.6f}")
            
            if not (ecart_somme < tolerance and ecart_moyenne < tolerance):
                errors.append(
                    f"Écart détecté pour '{col}':\n"
                    f"  Somme - CSV: {csv_sum:.6f}, Mongo: {mongo_sum:.6f}, Écart: {ecart_somme:.2e}\n"
                    f"  Moyenne - CSV: {csv_mean:.6f}, Mongo: {mongo_mean:.6f}, Écart: {ecart_moyenne:.2e}"
                )
    
    if errors:
        assert False, "\n".join(errors)

def test_sampling_integrity(dataframes):
    """Test d'intégrité par échantillonnage pour validation supplémentaire"""
    df_csv, mongo_stats = dataframes
    
    # Test uniquement si le dataset est assez grand
    if len(df_csv) < 100:
        pytest.skip("Dataset trop petit pour l'échantillonnage")
    
    # Échantillonnage du CSV
    sample_size = min(1000, len(df_csv) // 10)  # 10% ou 1000 max
    csv_sample = df_csv.sample(n=sample_size, random_state=42)
    
    # Échantillonnage MongoDB
    if _loader.collection is None:
        _loader.setup_mongodb_connection()
    
    mongo_sample = list(_loader.collection.aggregate([
        {"$sample": {"size": sample_size}}
    ]))
    
    mongo_sample_df = pd.DataFrame(mongo_sample).drop(columns=["_id"], errors="ignore")
    
    # Comparaison des distributions
    numeric_columns = csv_sample.select_dtypes(include=['number']).columns
    
    for col in numeric_columns:
        if col in mongo_sample_df.columns:
            csv_mean = csv_sample[col].mean()
            mongo_mean = mongo_sample_df[col].mean()
            
            # Tolérance plus large pour l'échantillonnage
            relative_diff = abs(csv_mean - mongo_mean) / csv_mean if csv_mean != 0 else 0
            
            assert relative_diff < 0.1, \
                f"Distribution différente pour {col}: CSV_mean={csv_mean:.2f}, " \
                f"Mongo_mean={mongo_mean:.2f}, Diff={relative_diff:.2%}"

# Tests de performance (optionnels)
def test_performance_benchmark():
    """Benchmark des performances de requête MongoDB"""
    if _loader.collection is None:
        _loader.setup_mongodb_connection()
    
    start_time = time.time()
    
    # Test de requête simple
    count = _loader.collection.count_documents({})
    
    # Test de requête avec filtre
    filtered_count = _loader.collection.count_documents({"Age": {"$gte": 30}})
    
    # Test d'agrégation
    avg_age = list(_loader.collection.aggregate([
        {"$group": {"_id": None, "avg_age": {"$avg": "$Age"}}}
    ]))[0]['avg_age']
    
    execution_time = time.time() - start_time
    
    logger.info(f"Benchmark MongoDB - Temps: {execution_time:.3f}s, "
               f"Total: {count}, Filtré: {filtered_count}, Âge moyen: {avg_age:.1f}")
    
    # Vérification que les performances sont acceptables (< 5 secondes)
    assert execution_time < 5.0, f"Performances MongoDB trop lentes: {execution_time:.2f}s"

if __name__ == "__main__":
    # Exécution des tests avec pytest
    pytest.main([__file__, "-v", "--tb=short"])