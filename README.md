# 📦 Projet de migration vers MongoDB avec Docker

Ce projet a pour objectif de migrer un jeu de données vers une base MongoDB à l'aide d'un script Python exécuté dans un conteneur Docker. Des tests d'intégrité sont également lancés automatiquement à la suite de la migration.

## 🧱 Structure du projet
```bash
projet-migration-mongodb/
│
├── scr/
│ └── migration.py # Script de migration
│
├── tests/
│ └── test_integrite.py # Tests d'intégrité de la migration
│
├── requirements.txt # Dépendances Python
├── Dockerfile # Image Docker pour Python
├── docker-compose.yml # Orchestration des conteneurs
├── README.md # Documentation
└── init.sh # rôles utilisateurs
```

## ⚙️ Prérequis

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/)

## 🔒 Sécurité

Les scripts et la base de données MongoDB sont protégés et restreint aux utilisateurs ayant l'identifiant et le mot de passe.

## 🚀 Lancer le projet

### 1. Cloner le dépôt

```bash
git clone https://github.com/votre-utilisateur/projet-migration-mongodb.git
cd projet-migration-mongodb
```

### 2. Lancer les conteneurs

```bash
docker compose up --build
```
Cela va :
 - Démarrer un conteneur MongoDB (mongo-container)
 - Construire l'image Docker de l'application (migrateur)
 - Lancer le script de migration (scr/migration.py)
 - Exécuter les texts d'intégrité (tests/test_integrite.py)

## 🧪 Tester manuellement la base MongoDB

Ouvrez un terminal interactif dans le conteneur MongoDB :
```bash
docker exec -it mongo-container mongosh
```

Puis exécutez par exemple : 
```bash
use base
db.ma_collection.find().pretty()
```

## 🧹 Pour nettoyer les conteneurs
```bash
docker compose down
```

## 🔎 Détails migration et tests

### 1. Migration - **migration.py**
Ce script automatise le téléchargment, le traitement et l'insertion du dataset dans une base MongoDB.\
a. Il télécharge le dataset en format CSV avec l'API Kaggle.\
b. Il charge les données dans un DataFrame Pandas. \
c. Il effectue un nettoyage basique : conversion des noms en majuscules et transformation des colonnes dates en format datetime.\
d. Il se connecte à une instance MongoDB (dont les identifiants sont récupérés via variables d'environnement).\
e. Il attend que MongoDB soit prêt avant d'insérer les données dans une collection.

### 2. Tests - test_integrite.py
Ce script contient une suite de tests automatisés pour vérifier la cohérence des données entre un fichier CSV et une collection MongoDB.\
a. Il appelle la migration à partir du script de migration.\
b. Il charge le dataset en format CSV avec l'API Kaggle et prépare les données CSV (mise en majuscules, conversion des dates).\
c. Il appelle la fonction permettant de récupérer les statistiques issues de MongoDB.\
d. Il vérifie :
 - Que le nombre d'enregistrements est identique entre CSV et MongoDB.
 - Que les colonnes présentes dans les deux sources sont les mêmes.
 - Que la somme et la moyenne des colonnes numériques sont identiques.
 - Que les distributions d'échantillions de chaque source soient semblables.

## 🗺️ Schéma base de données MongoDB
```bash
{
    _id: ObjectId(),
    Name: String,
    Age: Int,
    Gender: String,
    Blood Type: String,
    Medical Condition: String,
    Date of Admission: Datetime,
    Doctor: String,
    Hospital: String,
    Insurance Provider: String,
    Billing Amount: Float,
    Room Number: Int,
    Admission Type: String,
    Discharge Date: Datetime,
    Medication: String,
    Test Results: String
  }
```
