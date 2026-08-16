# FEC SCAN PRO 

**L'Audit Comptable Automatisé.**

Ce projet est une solution Fullstack (Django / React) permettant d'analyser les Fichiers des Écritures Comptables (FEC) pour détecter instantanément les anomalies fiscales et comptables.
# FEC SCAN — Plateforme d'Audit et de Détection d'Anomalies FEC

Solution applicative d'ingestion, d'audit fiscal et d'analyse prédictive des Fichiers des Écritures Comptables (FEC) conforme aux exigences de la DGFiP, développée dans le cadre de la certification Bachelor 3 Intelligence Artificielle & Data.

---

## 1. Informations Générales et Accès Publics

* **Nom du projet :** FEC SCAN
* **Périmètre académique :** Projet annuel de certification B3 IA & Data
* **URL publique de l'application :** `https://fecscan.fr`
* **Dépôt Git du code source :** `https://github.com/Romain-Y/FEC_SCAN_PRO`

---

## 2. Architecture Technique et Stack Logicielle

* **Couche Présentation (Frontend) :** React, Tailwind CSS, Vite
* **Couche Métier et API (Backend) :** Python 3.10+, Django REST Framework
* **Moteur d'Audit et Data Processing :** Pandas, NumPy
* **Base de Données Relationnelle :** PostgreSQL 14+ (persistance des dossiers, historisation des audits et traçabilité des anomalies)
* **Validation Multi-Navigateurs :** Google Chrome, Mozilla Firefox, Apple Safari, Microsoft Edge

---

## 3. Prérequis et Dépendances Système

* **Python :** Version 3.10 ou supérieure
* **Node.js :** Version 18.x ou supérieure (avec gestionnaire de paquets `npm`)
* **Serveur SQL :** PostgreSQL 14 ou supérieur en fonctionnement local ou distant

---

## 4. Procédure d'Installation et d'Exécution

```bash
# 1. Récupération des sources
git clone [https://github.com/Romain-Y/FEC_SCAN_PRO.git](https://github.com/Romain-Y/FEC_SCAN_PRO.git)


# 2. Initialisation de la base de données PostgreSQL
psql -U postgres -c "CREATE DATABASE fec_scan_db;"
psql -U postgres -d fec_scan_db -f ./database/dump_fec_scan.sql

# 3. Configuration et exécution de l'environnement Backend (Django)
cd backend
python -m venv venv
# Activation sous Windows :
venv\Scripts\activate
# Activation sous Linux/macOS :
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 4. Configuration et exécution du Frontend (React)
# Dans un second terminal, depuis la racine du projet :
cd frontend
npm install
npm run dev
---

##  Fonctionnalités Actuelles

### 1. Analyse Structurelle
- Vérification de la conformité du format FEC (normes DGFiP).
- Détection des ruptures de séquences (numérotation des pièces, dates).
- Contrôle de l'équilibre des journaux.

### 2. Audit Métier & Fiscal (Règles Implémentées)
- **Détection de la TVA Manquante** : Scan des comptes de charges (Classe 6) pour identifier les écritures n'ayant pas de TVA déductible associée (risque de perte fiscale).
- **Chasse aux Doublons** : Identification des écritures ayant strictement les mêmes attributs (Date, Journal, Montant, Libellé) pour éviter les doubles paiements.
- **Analyse des Écritures Atypiques** :
  - Détection des **montants ronds** (ex: 5000.00 €), souvent signe d'une estimation ou d'une absence de facture.
  - Repérage des écritures passées le **dimanche ou les jours fériés**.
- **Contrôle des Dates** : Vérification de la chronologie et de la cohérence entre la date de comptabilisation et la date de pièce.
- **Validation des Libellés** : Recherche de libellés vides ou peu explicites ("Divers", "Régul") qui ne respectent pas les normes FEC.

### 3. Reporting
- Génération automatique d'un rapport d'audit au format Excel.
- Visualisation des KPI clés via une interface web interactive.


## Stack Technique

- **Langage** : Python 3.13
- **Backend** : Django (Structure et API)
- **Frontend**: React (Interface finale)
- **Analyse de Données** : Pandas
