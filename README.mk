# FEC SCAN PRO 

**L'Audit Comptable Automatisé.**

Ce projet est une solution Fullstack (Django / React / Streamlit) permettant d'analyser les Fichiers des Écritures Comptables (FEC) pour détecter instantanément les anomalies fiscales et comptables.

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

---

## Roadmap (Évolutions Futures)

L'objectif est de passer d'un audit "Passif" à un audit "Actif" pour faire gagner du temps aux experts-comptables.

- [ ] **Génération d'OD de Correction** : Export automatique d'un fichier d'écritures (format TRA/CSV) importable directement dans Cegid/Sage pour corriger les erreurs sans ressaisie manuelle.
- [ ] **Deep Linking (SaaS)** : Pour les logiciels web (Pennylane, Tiime), ajout de liens directs vers l'écriture comptable incriminée pour une correction en 1 clic.

---

## Stack Technique

- **Langage** : Python 3.13
- **Backend** : Django (Structure et API)
- **Frontend / Data Viz** : Streamlit (Protopytage rapide), React (Interface finale)
- **Analyse de Données** : Pandas
