# DevScope
### Plateforme d'analyse des profils de développeurs GitHub

[English](README.md) | [Français](README.fr.md)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy"/>
  <img src="https://img.shields.io/badge/Scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="Scikit-learn"/>
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly"/>
</p>

<p align="center">
  <strong>Collecter. Traiter. Analyser. Découvrir.</strong>
</p>

---

## Présentation

**DevScope** est une application web basée sur Flask, conçue pour collecter, organiser, explorer et comparer des profils publics de développeurs GitHub.

L'application combine un processus ETL, la gestion d'une base de données relationnelle, des analyses interactives, la recherche de profils, l'exportation de données et une fonctionnalité expérimentale de mise en correspondance avec des offres d'emploi assistée par Machine Learning.

Elle transforme les informations publiques disponibles sur GitHub en données structurées et en résultats analytiques à travers une interface web intégrée.

Développé dans le cadre d'un projet académique, DevScope réunit des concepts pratiques du **Data Engineering, de l'analyse de données et du Machine Learning**.

## Fonctionnalités

### 01. Authentification et gestion des utilisateurs

- Inscription, connexion et déconnexion des utilisateurs.
- Hachage sécurisé des mots de passe.
- Collections de profils et favoris propres à chaque utilisateur.
- Historique des recherches et suivi des opérations sur les profils.
- Contrôle d'accès aux profils associés à l'espace de travail de chaque utilisateur.

### 02. Collecte de données GitHub

Collecte d'informations publiques sur les développeurs à l'aide de l'API REST GitHub.

L'application récupère notamment les informations suivantes :

- Nom d'utilisateur GitHub et nom affiché.
- Biographie et localisation.
- URL du profil et avatar.
- Nombre d'abonnés et nombre de dépôts publics.
- Informations relatives aux dépôts publics.
- Métadonnées des langages utilisés dans les dépôts.
- Informations disponibles sur les contributions et l'activité.

Un Personal Access Token GitHub peut être configuré de manière facultative afin de bénéficier de limites de requêtes API plus élevées.

### 03. Pipeline ETL

DevScope implémente un processus Extract, Transform, Load (ETL) pour traiter les données des développeurs GitHub.

| Étape | Opérations |
|---|---|
| **Extract (Extraction)** | Rechercher des utilisateurs GitHub et récupérer les informations publiques des profils et des dépôts. |
| **Transform (Transformation)** | Normaliser les champs, gérer les valeurs manquantes, supprimer les profils en double et dériver des indicateurs technologiques et d'activité. |
| **Load (Chargement)** | Créer ou mettre à jour les enregistrements des développeurs et associer les profils collectés à l'utilisateur à l'origine de la demande. |

Le pipeline enregistre également les informations relatives à son exécution, notamment le nombre d'éléments traités, les statuts et les journaux.

### 04. Tableau de bord interactif et analyses

Le tableau de bord présente une vue d'ensemble des données collectées sur les développeurs à travers :

- Les indicateurs clés de performance (KPI).
- Les statistiques des profils collectés.
- La répartition des technologies.
- Les indicateurs d'activité des développeurs.
- Les informations relatives aux localisations et aux plateformes.
- L'évolution du nombre de profils et d'autres indicateurs analytiques.
- Les résumés des collectes et des activités récentes.

Les visualisations interactives permettent aux utilisateurs d'explorer et d'interpréter les informations collectées.

### 05. Recherche de développeurs et gestion des profils

- Rechercher des profils par nom d'utilisateur, nom affiché ou localisation.
- Filtrer par technologie, plateforme, activité, période, nombre de dépôts et nombre d'abonnés.
- Trier et paginer les résultats de recherche.
- Consulter les détails des développeurs et les technologies détectées.
- Ajouter des profils aux favoris.
- Mettre à jour ou supprimer des profils d'un espace de travail personnel.
- Consulter les opérations effectuées sur les profils.

### 06. Comparaison des profils et mise en correspondance avec des offres d'emploi

L'application propose une fonctionnalité de comparaison des profils ainsi qu'un module expérimental de mise en correspondance avec des offres d'emploi.

Les utilisateurs peuvent spécifier :
- Un intitulé de poste.
- Les technologies requises.
- Les compétences requises.
- Un niveau d'expérience.

Le processus de mise en correspondance combine :
- Le chevauchement des compétences requises.
- Un score expérimental issu d'un modèle de Machine Learning.
- Un score lié à l'expérience.

Les résultats présentent une liste classée de profils de développeurs selon ces indicateurs.

### 07. Exportation des données

Exporter les informations du tableau de bord et des développeurs dans différents formats :

| Format | Utilisation |
|---|---|
| CSV | Exportation des informations tabulaires. |
| Excel (.xlsx) | Exportation des données structurées pour des analyses complémentaires. |
| PDF | Génération de rapports du tableau de bord et de rapports individuels des développeurs. |

### 08. Administration

Un espace d'administration en lecture seule fournit des informations de suivi concernant :

- Les utilisateurs inscrits.
- Les profils de développeurs collectés.
- Les technologies.
- Les exécutions ETL et les journaux.
- Les statistiques générales de l'application.

L'accès administrateur est contrôlé à travers le champ `is_admin` de la base de données de l'utilisateur.

---

## Technologies utilisées

| Catégorie | Technologies |
|---|---|
| **Langage de programmation** | Python |
| **Framework Backend** | Flask |
| **ORM et intégration de base de données** | Flask-SQLAlchemy, SQLAlchemy |
| **Frontend** | HTML, CSS, JavaScript, Jinja |
| **Traitement des données** | Pandas, NumPy |
| **Collecte des données** | GitHub REST API, Requests, BeautifulSoup |
| **Base de données** | SQLite, MySQL |
| **Visualisation des données** | Plotly, Matplotlib |
| **Machine Learning** | Scikit-learn |
| **Techniques de ML** | TF-IDF, Régression logistique, K plus proches voisins, Forêt aléatoire |
| **Exportation des données** | OpenPyXL, ReportLab |
| **Persistance des modèles** | Joblib |

---

## Architecture de l'application

DevScope suit une architecture modulaire qui sépare les routes de l'application, la logique métier, le traitement des données et la persistance.

```mermaid
flowchart TD
    A["Utilisateur / Navigateur"] --> B["Routes Flask et Templates Jinja"]
    B --> C["Services de l'application"]

    C --> D["Pipeline ETL GitHub"]
    D --> E["API REST GitHub"]
    D --> F["Pages publiques des profils GitHub"]

    C --> G["ORM SQLAlchemy"]
    G --> H[("Base de données SQLite / MySQL")]

    C --> I["Services analytiques"]
    C --> J["Services d'exportation"]
    C --> K["Ingénierie des caractéristiques ML et mise en correspondance"]

    I --> B
    J --> B
    K --> B
```

### Principaux modules de l'application

| Module | Responsabilité |
|---|---|
| `etl/` | Collecte des données GitHub et orchestration du pipeline ETL. |
| `ml/` | Ingénierie des caractéristiques, entraînement des modèles, prédiction et mise en correspondance des profils. |
| `models/` | Modèles de base de données et relations. |
| `routes/` | Authentification, pages de l'application, points de terminaison API et administration. |
| `services/` | Analyses, recherche, exportations, authentification et gestion des profils. |
| `templates/` | Pages HTML rendues avec Jinja. |
| `static/` | Fichiers CSS, JavaScript et icônes de l'interface. |

---

## Approche Machine Learning

Le composant de Machine Learning explore la classification des profils de développeurs et la mise en correspondance avec des offres d'emploi.

### Modèles de classification

Le module d'entraînement expérimente trois algorithmes de classification :

- Régression logistique (Logistic Regression).
- K plus proches voisins (KNN).
- Forêt aléatoire (Random Forest).

### Ingénierie des caractéristiques

Le pipeline de caractéristiques combine des indicateurs numériques des profils, notamment :

- Nombre d'abonnés.
- Nombre de dépôts publics.
- Contributions.
- Ancienneté du compte.
- Activité récente.
- Nombre de technologies détectées.

Il utilise également des caractéristiques TF-IDF dérivées des langages des dépôts et des compétences détectées.

### Limite méthodologique importante

Le processus d'entraînement actuel génère sa cible `high_quality` à l'aide d'un seuil de percentile appliqué au `global_score` pondéré propre à l'application.

Puisque ce score est lui-même calculé à partir des indicateurs des profils utilisés par le modèle, le composant ML constitue une approximation expérimentale d'une règle de scoring interne.

Il **n'est pas entraîné sur des résultats de recrutement étiquetés indépendamment ni sur des données vérifiées relatives à la qualité des développeurs**.

Par conséquent, ses métriques et ses scores de mise en correspondance doivent être interprétés comme des indicateurs exploratoires d'aide à la décision, et non comme une preuve de précision en matière de recrutement ou comme une décision automatisée d'embauche.

---

## Structure du projet

```text
DevScope/
│
├── backend/
│   ├── app/
│   │   ├── etl/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── static/
│   │   └── templates/
│
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
│
├── .gitignore
└── README.md
```

---

## Installation et configuration

### Prérequis

- Python 3.11 (recommandé).
- Git.
- Une connexion Internet pour la collecte des données GitHub.
- Un GitHub Personal Access Token (facultatif).

La base de données par défaut est SQLite. Un serveur de base de données distinct n'est donc pas nécessaire pour une exécution locale.

### 1. Cloner le dépôt

```bash
git clone https://github.com/yasmine-salama/DevScope.git
cd DevScope
```

### 2. Accéder au dossier Backend

```bash
cd backend
```

### 3. Créer un environnement virtuel

```bash
python -m venv .venv
```

L'activer sous Windows :

```powershell
.venv\Scripts\Activate.ps1
```

Sous macOS / Linux :

```bash
source .venv/bin/activate
```

### 4. Installer les dépendances

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurer les variables d'environnement

Créer un fichier `.env` local à partir du fichier d'exemple fourni.

**Windows (PowerShell) :**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux :**

```bash
cp .env.example .env
```

Ouvrir `.env` et configurer les paramètres nécessaires :

```dotenv
SECRET_KEY=your_generated_secret_key
DATABASE_URL=sqlite:///devscope.db
GITHUB_TOKEN=
SESSION_COOKIE_SECURE=false
```

Générer une clé secrète sécurisée avec :

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Clé secrète obligatoire utilisée pour signer les sessions Flask. Elle doit contenir au moins 32 caractères. |
| `DATABASE_URL` | URL de connexion à la base de données. SQLite est utilisé par défaut. |
| `GITHUB_TOKEN` | Token GitHub facultatif pour les requêtes API authentifiées. |
| `SESSION_COOKIE_SECURE` | Activer les cookies de session sécurisés lorsque l'application est accessible via HTTPS. |

Pour utiliser MySQL, configurer une URL de connexion SQLAlchemy :

```dotenv
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE_NAME
```

**Sécurité :** ne jamais publier le fichier `.env`, le token GitHub, les mots de passe ou les clés secrètes.

### 6. Lancer l'application

Depuis le dossier `backend/` :

```bash
python run.py
```

Ouvrir l'application dans le navigateur :

```text
http://127.0.0.1:5000
```

Le schéma de la base de données est initialisé au démarrage de l'application.

Le serveur Flask intégré est destiné au développement local et non à un déploiement en production.

---

## Utilisation de DevScope

1. Ouvrir l'application et créer un compte utilisateur.
2. Se connecter et accéder au tableau de bord.
3. Utiliser les fonctionnalités de recherche et de collecte GitHub pour trouver des profils publics de développeurs.
4. Lancer une collecte ETL avec une requête de recherche et une limite de profils adaptée.
5. Explorer les profils collectés à travers les sections Search et Developer Details.
6. Ajouter les profils intéressants aux favoris.
7. Comparer les profils de développeurs sélectionnés.
8. Explorer le modèle ML expérimental et la fonctionnalité de mise en correspondance avec des offres d'emploi.
9. Exporter les informations du tableau de bord ou des profils aux formats CSV, Excel ou PDF.
10. Consulter l'historique des exécutions ETL et les journaux.

La collecte GitHub dépend de la disponibilité du réseau et des limites de requêtes de l'API. Le token est facultatif, mais recommandé pour les collectes répétées.

---

## Tests

Les tests fonctionnels sont disponibles dans le dossier Backend.

Les exécuter avec :

```bash
python -m unittest discover -s tests -v
```

Les tests couvrent les principaux flux de l'application, notamment l'isolation des données des utilisateurs, le comportement ETL avec des réponses GitHub simulées, les pages ML et les points de terminaison d'exportation.

Ils ne remplacent pas un audit complet de sécurité ni des tests d'acceptation en production.

---

## Limites connues

- Les informations relatives aux contributions GitHub sont récupérées depuis les pages publiques des profils et peuvent devenir indisponibles si GitHub modifie leur structure.
- Les technologies détectées sont déduites des métadonnées des langages dans un ensemble limité de dépôts publics ; elles ne constituent pas un inventaire complet ou vérifié des compétences.
- Les limites de l'API GitHub et la disponibilité du réseau peuvent interrompre la collecte des données.
- Les scores ML dépendent du jeu de données disponible et de l'approche heuristique utilisée pour générer les cibles.
- Le dépôt ne contient ni base de données préremplie ni modèle entraîné. Ces éléments sont générés localement lors de l'utilisation de l'application.
- L'application est un projet académique/de démonstration et n'est pas renforcée pour un déploiement multi-utilisateur en production.

---

## Améliorations futures

- Étendre la couverture des tests unitaires et d'intégration.
- Introduire une protection CSRF et une limitation du nombre de tentatives de connexion.
- Améliorer les mécanismes de nouvelle tentative et de temporisation progressive des requêtes à l'API GitHub.
- Ajouter des contrôles de conservation des données et une meilleure traçabilité de leur provenance.
- Améliorer l'évaluation ML à l'aide de labels indépendants et vérifiés.
- Améliorer la configuration du déploiement et la prise en charge de WSGI en production.

---

## Auteur

**Yasmine Salama**

Étudiante en Sciences des Données | Data Engineering

[Profil GitHub](https://github.com/yasmine-salama)

[Dépôt DevScope](https://github.com/yasmine-salama/DevScope)

---

<p align="center">
  <strong>DevScope</strong><br/>
  <sub>Collecter. Traiter. Analyser. Découvrir.</sub>
</p>
