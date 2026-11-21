# Guide détaillé des fonctionnalités — DevScope (FR)

Ce document décrit en détail toutes les fonctionnalités visibles dans l'interface, le rôle de chaque bouton/élément et le rôle de chaque étape (ETL, ML, matching, comparaison), afin de faciliter l'utilisation, la maintenance et la rédaction de la documentation technique finale.

---

## 1. Vue d'ensemble
L'application DevScope permet de collecter, nettoyer et analyser des profils développeurs (principalement depuis GitHub), de stocker ces profils localement, d'effectuer des recherches avancées, de sauvegarder des favoris, de suivre l'historique d'extractions (ETL) et d'exploiter des modules de Machine Learning pour le classement et le matching.

Pages principales accessibles depuis la sidebar :
- Dashboard
- Search
- Favorites
- ETL History
- ML Dashboard
- Job Matching
- Comparaison Profils

Fichiers clés (références) :
- Template layout principal : [backend/app/templates/layout/base.html](backend/app/templates/layout/base.html)
- Styles globaux : [backend/app/static/css/app.css](backend/app/static/css/app.css)
- Scripts front (comportements UI) : [backend/app/static/js/app.js](backend/app/static/js/app.js)
- ETL & ML : [backend/app/etl](backend/app/etl)
- ML training : [backend/app/ml/model_training.py](backend/app/ml/model_training.py)
- Feature engineering : [backend/app/ml/feature_engineering.py](backend/app/ml/feature_engineering.py)
- Matching : [backend/app/ml/matching_service.py](backend/app/ml/matching_service.py)

---

## 2. Navigation & Topbar

### Sidebar
- `Dashboard` : accès à la page principale de synthèse et d'actions ETL.
- `Search` : recherche live GitHub et recherche dans la base locale avec filtres.
- `Favorites` : profils que l'utilisateur a sauvegardés.
- `ETL History` : tableau des exécutions ETL (détails par run).
- `Machine Learning` (sous-section) : `ML Dashboard`, `Job Matching`, `Comparaison Profils`.
- `Admin` (visible seulement pour les comptes admin) : pages d'administration.

Tous les liens utilisent des routes Flask : voir `backend/app/routes/pages.py`.

### Topbar
- Bouton menu (`sidebarToggle`) : bascule l'affichage du sidebar (utile sur mobile).
- Champ `Global search` : recherche rapide (redirige vers `/search?q=...`).
- Bouton notifications (`notificationsBtn`) : déclenche l'affichage des toasts/notifications (front simplifié : toasts gérés par `toast()` dans `app.js`).
- `Toggle theme` (`themeToggle`) : bascule entre mode sombre / clair (persisté dans `localStorage`).
- Icône profil : lien vers la page `Profile` de l'utilisateur connecté (`pages.profile`).

---

## 3. Dashboard
Objectif : synthèse des KPIs, contrôle de l'ETL, visualisations Plotly et accès rapide aux listes de profils.

Principaux blocs et boutons :

### ETL Control (carte)
- `GitHub Search Query` (input) : phrase de recherche utilisée pour les runs ETL (ex : "location:Morocco language:Python").
- `Limit` (input number) : nombre maximal de profils à extraire sur ce run.
- `Run ETL` (`btn btn-primary`) : déclenche un POST vers `/api/etl/run` (via `app.js`) pour lancer un job ETL ; pendant l'exécution le bouton est désactivé et l'état est mis à jour.
- `etlStatusPill` : indique l'état actuel (Idle / Running / Success / Failed).
- `etlMonitor` : volet visuel qui affiche des métriques de la dernière exécution (extracted, transformed, loaded, duplicates removed, error count, durée). Les valeurs proviennent de `/api/etl/history` ou `/api/etl/last`.

Rôle de chaque étape ETL (qu'on visualise ici) :
1. Extract : rechercher et récupérer les données brutes depuis l'API GitHub ou autre source.
2. Transform : dédupliquer, normaliser, enrichir et nettoyer les données (par ex. calculer `skills_list`, `global_score`).
3. Load : écrire dans la base locale (SQLAlchemy) les profiles nettoyés et indexés.

### KPI Grid
- `Profiles` : nombre total de profils stockés. (affiché et animé par `animateNumber()`)
- `Active (30d)` : estimation de profils actifs dans les derniers 30 jours.
- `Data Quality` : métrique composite (couverture `location` + `bio`) et barre de progression.
- `Favorites` : nombre de profils sauvegardés.

### Insights (carte)
- `Top language`, `Top location`, `Recent growth` : extraits automatiques produits côté backend (endpoint `/api/dashboard/summary`) ou calculés en JS pour fournir des indications rapides.

### Analytics (charts)
Cartes Plotly pour : Top Technologies, Activity Over Time, Platform Distribution, Profile Growth, Followers vs Repositories, Activity Freshness, Data Completeness, ETL Throughput.
- Chaque `div` chart est rendu via `Plotly.newPlot(...)` en JS avec les payloads fournis par `/api/dashboard/charts`.
- Les graphiques sont responsives et utilisent des layouts par défaut (police, marges) définis dans le JS.

### Profiles lists
- `Top Developers`, `Most Active Profiles`, `Recent Collected Profiles` : listes affichées sous forme compacte (avatar + meta + bouton `View`/`Open`).
- `View/Open` : lien vers la page `developer_details` (`/developers/<id>`).

---

## 4. Search
Deux zones :
1. GitHub Live Search (direct) — requêtes vers l'API GitHub
2. Local Database Search — filtres et tri sur la base locale

### GitHub Live Search
- Input `GitHub username` et `limit` : permet de récupérer rapidement des profils public GitHub sans lancer l'ETL.
- `Search GitHub` : déclenche un call `/api/github/users?q=...&limit=...`.
- Résultats affichés en cartes (`github-card`) contenant : avatar, pseudo, bio, stats (followers, repos), actions `Open` (ouvre profil GitHub) et `Save` (enregistre local via `/api/github/users/save`).

### Local Database Search
- Input principal : `searchInput` (username, name, location...) + boutons `Search` et `Reset`.
- Filtres disponibles :
  - `Technologies` (free text)
  - `Platform` (ex: GitHub)
  - `Activity` (high/medium/low)
  - `Recent days` (7,30,90,...)
  - `Location`
  - `Repositories` min/max
  - `Followers` min/max
  - `Sort` (activity, followers, repos, name, updated) et `Order` (asc/desc)
- `activeTags` : barre de tags qui récapitule les filtres actifs et permet de supprimer un filtre d'un clic.
- `Results` : affichés en cartes professionnelles (`result-card`) contenant : avatar, nom, meta (platform, repos, followers), badge d'activité (high/medium/low), `View` (lien profil) et `Save/Remove` (toggle favoris via `/api/favorites`).
- `Pagination` : navigation paginée (Prev/Next) et boutons numériques.
- `Recent Searches` : chips pour recharger les recherches précédentes (stockées via `/api/search/history`).

Rôle des étapes de recherche :
- Collecter les filtres -> construire URL params -> appeler `/api/search` -> rendre les cartes -> gérer pagination et tags.

---

## 5. Favorites
Objectif : composer une liste de profils intéressants et offrir des outils de comparaison rapide.

Composants :
- Overview KPIs : `Total`, `Avg Followers`, `Avg Repos` (calculés via `/api/favorites/stats` ou via requêtes individuelles si endpoint absent).
- `Compare Favorites` : bouton qui ouvre la vue de comparaison (`/ml/compare?ids=...`) pour les profils sélectionnés.
- Results grid : mêmes `result-card` que sur la page de recherche, actions `View` et `Remove`.

Rôle : facilement retrouver et comparer profils déjà sauvegardés.

---

## 6. ETL History
Page contenant un tableau des exécutions ETL (dernier run en haut).

Colonnes & signification :
- `ID` : identifiant du run.
- `Source` : source (ex: GitHub search query).
- `Status` : success / failed / running.
- `Extracted` : nombre d'items extraits.
- `Transformed` : nombre après nettoyage.
- `Loaded` : nombre insérés en base.
- `Duration` : durée d'exécution (s).
- `Duplicates` : nombre d'entrées dédupliquées.
- `Errors` : nombre d'erreurs rencontrées.
- `Started` : date et heure de début.

Interactions :
- Aucune action lourde par défaut ; l'interface est informative. Certains boutons administratifs peuvent permettre de relancer un run si implémenté côté API.

---

## 7. ML Dashboard
Objectif : surveiller l'état des modèles ML, comparer algorithmes, afficher l'importance des features.

Composants & boutons :
- KPI grid : `Total Profiles`, `Production Model`, `Accuracy`, `F1 Score`.
- `Model Comparison` (chart) : visualise métriques (accuracy, f1, precision, recall) par algorithme.
- `Feature Importance` : bar chart des features les plus importantes (ex : followers_count, repos_count, certaines compétences).
- `Top Signals` : insights textuels (squelette si données manquantes).
- `(Re)Train models` : bouton qui mène à la route `ml.train` (ou déclenche côté backend la procédure de training). En pratique, le training est orchestré par `backend/app/ml/model_training.py` et sauvegarde le meilleur pipeline via `joblib` (fichier `instance/ml/best_model.joblib`).

Rôle de chaque étape ML :
1. Feature engineering : rassembler et transformer les variables (voir `feature_engineering.py`).
2. Training : tester plusieurs algorithmes (LogisticRegression, KNN, RandomForest...), comparer via métriques (Precision/Recall/F1), choisir et sauvegarder le meilleur pipeline.
3. Production : pipeline chargé par `prediction_service` pour prédire `ml_score` sur des profils.

---

## 8. Job Matching
Formulaire d'entrée et résultats détaillés pour recommander des candidats.

Formulaire :
- `Intitulé du poste` (title)
- `Technologies requises` (technologies, CSV)
- `Compétences requises` (skills, CSV)
- `Niveau d'expérience` (junior / mid / senior)
- `Top results` (nombre max de candidats retournés)
- `Weights` (poids skill / ml / experience) : permet d'ajuster la combinaison finale
- `Recommander` : lance le matching côté serveur via `ml.match` et renvoie un tableau de résultats.

Résultats (table améliorée) :
- `Rank` : position (1..N)
- `Username` : lien vers `developer_details`
- `Final score` : affiché avec une `progress-bar` et en pourcentage
- `Skill match` : % de compétences demandées présentes
- `Matched / Missing` : badges `good` (compétences trouvées) et `bad` (compétences manquantes)
- `ML score` : score prédictif du modèle (si disponible)
- `Exp. match` : adéquation expérience requise
- `Why recommended` (détails collapsibles) : montre la décomposition du scoring (skill / ml / experience)

Rôle de chaque étape :
- Skill matching : extraction et comparaison des `skills_list` du profil avec les compétences demandées.
- ML score : éventuel score prédictif indiquant la probabilité qu'un profil soit « high quality ».
- Experience scoring : adaptation selon `account_age_days` / `contributions_last_year`.
- Final score : combinaison pondérée et tri des candidats.

---

## 9. Comparaison Profils
Permet de sélectionner plusieurs profils (checkboxes) et d'afficher :
- Tableau récapitulatif des métriques (followers, repos, contributions)
- Graphiques Plotly : bar chart, radar chart, skill bar chart, heatmap des compétences
- Cartes résumé par profil (top metric)

Usage : sélectionner au moins 2 profils puis `Comparer la sélection`.

---

## 10. Developer Details (fiche profil)
Fiche détaillée d'un développeur (template `backend/app/templates/developer_details.html`)
Contient typiquement :
- Avatar & nom d'affichage, lien profil GitHub
- Bio, location, entreprise
- Bouton `Save` / `Remove` favoris
- Statistiques : followers, repos, contributions (1y), dernière activité
- Liste des skills (pills) avec score
- Repositories list (rows) avec stars/forks
- Graphiques : skills bar / skills pie

Action principale : `Save` ajoute le profil à `/api/favorites`.

---

## 11. Composants UI & Boutons (rôle)
- `btn-primary` : action principale (ex : Run ETL, Search, Save). Couleur pleine.
- `btn-ghost` : action secondaire (ex : Reset, Open, View). Apparence légère.
- `btn-icon` : boutons carrés pour icônes (sidebar toggle, theme, notifications).
- `btn-full` : bouton pleine largeur.
- `progress` / `progress-bar` : indicateurs visuels (pourcentage). Utilisés dans matching & quality bars.
- `card`, `card-head`, `card-body` : conteneurs uniformes pour cohérence visuelle.
- `skeleton` : placeholders animés pour états de chargement.
- `empty` / `empty-state` : état visuel quand aucune donnée n'est disponible.
- `toast()` : notifications temporaires côté client (succès/avertissement/erreur).

---

## 12. Endpoints utilisés par le front-end (rappel)
- `/api/github/users` : recherche GitHub (GET)
- `/api/github/users/save` : sauvegarde d'un profil GitHub (POST)
- `/api/dashboard/summary` : synthèse KPI pour dashboard (GET)
- `/api/dashboard/charts` : payloads Plotly pour charts (GET)
- `/api/etl/run` : déclenche un ETL (POST)
- `/api/etl/history` : historique des runs ETL (GET)
- `/api/search` : recherche dans la base locale (GET)
- `/api/search/history` : recherches récentes (GET)
- `/api/favorites` : liste des favoris (GET/POST/DELETE)
- `/api/favorites/stats` : statistiques agrégées sur favoris (GET) — endpoint toléré mais facultatif
- `/api/developers/<id>` : détails d'un developer (GET)
- `/api/developers/<id>/repos` : repos d'un developer (GET)
- Routes ML : `/ml/dashboard`, `/ml/train`, `/ml/match`, `/ml/compare` (BluePrint ml)

Note : certains endpoints frontales s'attendent à des réponses `data: {...}` ; voir `backend/app/static/js/app.js` pour la logique exacte de parsing et gestion d'erreur.

---

## 13. Flux de données & responsabilité de chaque étape
- Collecte (ETL Extract) : la page Dashboard permet de lancer une recherche et d'extraire des profils.
- Nettoyage (ETL Transform) : normalisation, suppression de duplicatas, calcul de métriques (ex : `global_score`) via `feature_engineering.py`.
- Stockage (ETL Load) : insertion en base, indexation des champs importants.
- Enrichissement ML : `model_training.py` génère pipelines, évalue et sauvegarde le meilleur modèle dans `instance/ml` via `joblib`.
- Exposition : endpoints REST fournissent données nécessaires au front (KPIs, charts, search, favorites).

---

## 14. Erreurs fréquentes et dépannage court
- `TemplateAssertionError: block 'scripts' defined twice` : vérifier doublons de `block scripts` dans le template (corrigé dans `backend/app/templates/ml/dashboard.html`).
- `PicklingError` lié à `lambda` dans pipeline : remplacer tokenizer lambda par fonction de niveau module (corrigé dans `backend/app/ml/model_training.py`).
- `BuildError` route manquante : vérifier que la route existe (`pages.profile` manquante a été ajoutée dans `backend/app/routes/pages.py`).

---

## 15. Conseils pour extension et bonnes pratiques
- Factoriser composants répétitifs en macros Jinja (`components/card.html`, `components/kpi.html`).
- Ajouter `Flask-Caching` sur endpoints lourds (`/api/dashboard/summary`, `/api/search`) avec TTL raisonnable.
- Ajouter tests d'intégration pour endpoints critiques (ETL, search, favorites, ml train).
- Documenter les payloads attendus pour les endpoints Plotly (formats `data` / `layout`) pour faciliter l'export et la visualisation.

---

## 16. Demandes possibles / prochaines actions
- Traduction du document en anglais.
- Export PDF du guide avec captures d'écran.
- Génération d'un styleguide + macros Jinja à partir des composants existants.

---

Document créé par l'équipe technique — version courte destinée à l'usage interne. Pour toute modification, indiquez les pages ou composants à détailler davantage.
