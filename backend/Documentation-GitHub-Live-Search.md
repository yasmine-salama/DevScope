# Documentation technique - Recherche GitHub en direct

## Integration GitHub API

La recherche en direct utilise l'API REST GitHub sans modifier le systeme ETL existant. Le service `app/services/github_live_service.py` appelle:

- `GET /search/users` avec `q=<username> in:login type:user` pour limiter la recherche aux usernames.
- `GET /users/{login}` pour recuperer les champs detailles affiches dans l'interface: avatar, username, bio, followers et nombre de depots publics.

Le token `GITHUB_TOKEN` reste optionnel dans `.env`. S'il est present, il est envoye dans l'en-tete `Authorization: Bearer ...` pour augmenter les limites d'API.

## Nouvelles routes

- `GET /api/github/users?q=<username>&limit=5|10`
  - Recherche 1 a 10 utilisateurs GitHub.
  - Retourne une liste normalisee de profils.
  - Renvoie `429` avec le code `github_rate_limit` si la limite GitHub est atteinte.

- `POST /api/github/users/save`
  - Sauvegarde ou met a jour un profil GitHub dans la table locale `developers`.
  - Corps JSON: `{ "username": "octocat" }`.
  - Cette route est optionnelle cote workflow utilisateur et ne lance pas l'ETL.

## Page et workflow de recherche

La page `/search` contient une nouvelle section "GitHub Live Search" separee de la recherche locale existante.

Workflow:

1. L'utilisateur saisit un username GitHub.
2. L'utilisateur choisit une limite de 5 ou 10 resultats.
3. La recherche est declenchee uniquement au clic sur le bouton "Search GitHub".
4. L'interface affiche un etat de chargement pendant l'appel API.
5. Les cartes resultats affichent avatar, username, bio, followers et repositories.
6. Le bouton "Save" permet d'enregistrer le profil dans la base locale.

## Optimisations utilisees

- Nombre de resultats limite a 10 maximum.
- Aucun appel GitHub automatique au chargement de la page.
- Requetes API uniquement apres clic utilisateur.
- Reutilisation du token `.env` deja supporte par la configuration.
- Gestion explicite des erreurs et des limites de taux GitHub.
- Architecture stable: ajout d'un service dedie, de routes API dediees et d'une section UI isolee, sans modification du pipeline ETL.
