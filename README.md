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
└── README.md # Documentation
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

### 2. Ajouter un fichier .env

Afin de pouvoir exécuter les scripts et accéder à la base de données MongoDB, vous devez ajouter dans le dossier un fichier **.env** contenant les identifiants et mots de passe.

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
