# DevScope — GitHub Developer Profile Analytics

DevScope is a Flask web application for collecting, organizing, exploring, and comparing **public GitHub developer profiles**. It combines a small ETL workflow, relational data storage, interactive analytics, profile search, exports, and experimental machine-learning-assisted job matching.

The project was developed as an academic internship/PFE application. This repository contains the application source code and technical documentation; local databases, credentials, virtual environments, and generated personal report material are intentionally excluded.

## Contents

- [What DevScope does](#what-devscope-does)
- [Main features](#main-features)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Repository structure](#repository-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Run the application](#run-the-application)
- [How to use it](#how-to-use-it)
- [Machine-learning approach and limitations](#machine-learning-approach-and-limitations)
- [Tests](#tests)
- [Data, privacy, and security](#data-privacy-and-security)
- [Known limitations](#known-limitations)
- [Future improvements](#future-improvements)
- [License](#license)

## What DevScope does

The application retrieves public developer information from the GitHub REST API, transforms selected fields, stores the results in a SQL database, and presents them through a web dashboard.

It is intended as a technical exploration of a complete data-oriented application workflow:

1. Collect public profile and repository information.
2. Clean and transform the collected data.
3. Store profiles and detected technologies in a relational database.
4. Explore profiles with search, filters, and analytics.
5. Compare profiles and experiment with job-to-profile matching.
6. Export selected information for further analysis.

## Main features

### 1. Authentication and user workspaces
- User registration, login, and logout.
- Passwords stored as password hashes (not plaintext).
- User-specific profile collections, favorites, and search history.
- Access checks for profiles associated with a user's workspace.

### 2. GitHub profile collection
- Search GitHub users by query.
- Retrieve public profile details and public repositories.
- Collect fields such as username, display name, bio, location, followers, public repository count, and profile URL.
- Derive a list of technologies from repository language metadata.
- Optionally use a GitHub personal access token to increase API rate limits.

### 3. ETL pipeline
- **Extract:** search GitHub and retrieve public user/repository data.
- **Transform:** normalize fields, handle missing values, remove duplicate profiles, derive activity and technology information.
- **Load:** create or update developer records and link collected profiles to the requesting user.
- Record ETL runs, processing counts, statuses, and logs.

### 4. Dashboard and analytics
- KPI cards for collected profiles, technologies, favorites, and data completeness.
- Interactive charts for technology distribution, activity, platform distribution, locations, profile growth, and other profile indicators.
- Recent collection and activity summaries.

### 5. Search and profile management
- Search by username, display name, or location.
- Filter by technology, platform, activity, date range, repository count, and follower count.
- Sort and paginate search results.
- Open profile details and inspect detected technologies and available repository information.
- Save favorites, update or remove profiles from a workspace, and review profile operations.

### 6. Comparison and job matching
- Compare selected developer profiles.
- Enter a job title, required technologies, required skills, and an experience level.
- Produce a ranked list using skill overlap, an experimental model score, and an experience-related score.

### 7. Exports
- Export dashboard/profile data as CSV.
- Export tabular data as Excel (`.xlsx`).
- Generate PDF reports for dashboard or individual profile information.

### 8. Administration
- Read-only administration pages for user, profile, ETL, and technology statistics.
- Admin access is controlled by the `is_admin` field in the database. New registrations are **not** automatically granted admin privileges.

## Technology stack

| Area | Technologies |
|---|---|
| Backend | Python, Flask, Flask-SQLAlchemy, SQLAlchemy |
| Frontend | HTML, CSS, JavaScript, Jinja templates |
| Data processing | Pandas, NumPy |
| Data collection | GitHub REST API, Requests, BeautifulSoup |
| Database | SQLite by default; MySQL can be configured through PyMySQL |
| Visualization | Plotly, Matplotlib |
| Machine learning | scikit-learn, TF-IDF, Logistic Regression, KNN, Random Forest |
| Exports | CSV, OpenPyXL, ReportLab |
| Model persistence | Joblib |

## Architecture

```mermaid
flowchart TD
    A["Browser"] --> B["Flask routes and Jinja templates"]
    B --> C["Application services"]
    C --> D["ETL collector"]
    D --> E["GitHub REST API"]
    D --> F["Public GitHub profile page"]
    C --> G["SQLAlchemy ORM"]
    G --> H[("SQL database")]
    C --> I["Analytics and export services"]
    C --> J["ML feature engineering and matching"]
    I --> B
    J --> B
```

The backend is organized around Flask blueprints, data models, and service modules. The ETL collector is separated from the pipeline orchestration, while analytics, exports, profile management, and ML functionality live in dedicated packages.

## Repository structure

```text
DevScope/
├── backend/
│   ├── app/
│   │   ├── etl/              # GitHub collection and ETL pipeline
│   │   ├── ml/               # Feature engineering, training, prediction, matching
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routes/           # Authentication, pages, API, administration
│   │   ├── services/         # Analytics, exports, search, profile services
│   │   ├── static/           # CSS, JavaScript, icons
│   │   └── templates/        # Jinja HTML templates
│   ├── docs/                 # Feature and GitHub collection notes
│   ├── tests/                # Functional integration tests
│   ├── .env.example          # Safe configuration template
│   ├── requirements.txt
│   └── run.py
├── docs/
│   ├── diagrams/             # Mermaid and PlantUML diagrams
│   ├── Documentation_ML_FR.md
│   └── Documentation_Technique_DevScope_FR.md
├── .gitignore
└── README.md
```

## Additional documentation

- [Technical documentation (French)](docs/Documentation_Technique_DevScope_FR.md)
- [Machine-learning documentation (French)](docs/Documentation_ML_FR.md)
- [Architecture and workflow diagrams](docs/diagrams/README.md)
- [Feature guide (French)](backend/docs/Guide_Fonctionnalites_FR.md)
- [GitHub live-search notes](backend/Documentation-GitHub-Live-Search.md)

## Requirements

- Python 3.11 is recommended.
- Git.
- Internet access for GitHub collection.
- A GitHub personal access token is optional; unauthenticated requests are subject to lower rate limits.

The default database is SQLite, so a separate database server is not required for a local run.

## Installation

Open a terminal in the repository and move into the backend directory:

```bash
cd backend
```

### Windows (PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Edit `backend/.env` and set a strong secret key. Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Example configuration:

```dotenv
SECRET_KEY=replace_with_a_random_64_character_hex_value
DATABASE_URL=sqlite:///devscope.db
GITHUB_TOKEN=
SESSION_COOKIE_SECURE=false
```

Configuration variables:

| Variable | Required | Description |
|---|---:|---|
| `SECRET_KEY` | Yes | Random secret of at least 32 characters used to sign Flask sessions. The app rejects the placeholder value. |
| `DATABASE_URL` | No | SQLAlchemy database URL. Defaults to SQLite (`sqlite:///devscope.db`). |
| `GITHUB_TOKEN` | No | GitHub token used for authenticated API requests and higher rate limits. |
| `SESSION_COOKIE_SECURE` | No | Set to `true` only when the application is served over HTTPS. Keep `false` for local HTTP development. |

For MySQL, install/use the included PyMySQL driver and set a SQLAlchemy URL such as:

```dotenv
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE_NAME
```

Do not commit `.env`, real tokens, database files, or passwords. The repository `.gitignore` excludes these local files.

### Admin account

Register a normal account first. To grant that account access to the read-only admin area, update its `is_admin` value in your local database. For the default SQLite setup, run this from the `backend` directory after replacing the email:

```bash
python -c "import sqlite3; c=sqlite3.connect('instance/devscope.db'); c.execute('UPDATE users SET is_admin=1 WHERE email=?', ('your-email@example.com',)); c.commit(); c.close()"
```

The application intentionally does not grant admin privileges merely because someone enters a configured email address during public registration.

## Run the application

From the `backend` directory, with the virtual environment activated:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000
```

The application initializes its database schema on startup. The built-in Flask server is for local development only; it is not a production deployment server.

## How to use it

1. Open the application and create an account.
2. Sign in and open the dashboard.
3. Use the GitHub search/collection controls to find public developer profiles.
4. Run an ETL collection with a query and a reasonable profile limit.
5. Explore the collected profiles through Search and Developer Details.
6. Save profiles to Favorites or compare selected profiles.
7. Open the ML area to train the experimental model or try job matching.
8. Export dashboard or profile information as CSV, Excel, or PDF.
9. Review collection runs and logs in ETL History.

GitHub collection depends on API availability and rate limits. A token is optional for local exploration but recommended for repeated collection.

## Machine-learning approach and limitations

The ML module currently experiments with three classifiers:

- Logistic Regression
- K-Nearest Neighbors
- Random Forest

The feature pipeline combines numerical profile indicators (followers, repositories, contributions, account age, recent activity, and detected technology count) with TF-IDF features derived from repository languages/skills.

**Important methodological note:** the current training code creates its `high_quality` target from a percentile threshold over the application's own weighted `global_score`. That score is itself calculated from profile indicators used by the model. Therefore, the ML task is a heuristic experiment that approximates the application's scoring rule; it is **not** trained on independently labelled hiring outcomes or verified developer quality. Its reported metrics should not be interpreted as proof of recruitment accuracy.

The job-matching module combines required-skill overlap, the saved model's score (when a model exists), and an experience-related component. Results are exploratory decision support only and should not be used as an automated hiring decision.

## Tests

From the `backend` directory:

```bash
python -m unittest discover -s tests -v
```

The functional tests cover key flows such as user data isolation, ETL behavior with mocked GitHub responses, ML pages, and export endpoints. They do not replace a full security review or production acceptance test.

## Data, privacy, and security

- The collector is designed to retrieve public GitHub profile and repository information.
- Public profile information can still be personal data. Collect only what is needed and respect GitHub's terms, API policies, and applicable privacy requirements.
- A GitHub token is a credential: keep it in `backend/.env` or a secure environment-variable store, never in source code.
- Passwords are stored using Werkzeug password hashing.
- User-specific profile access is enforced in the application services and routes.
- The repository excludes local databases, account records, generated model files, virtual environments, and local configuration.

Before exposing an instance to the internet, add and verify production controls such as CSRF protection for state-changing requests, login rate limiting, email verification or controlled account creation, HTTPS, secure secret management, database backups, and a production WSGI server. The current project is an academic/demo application, not a hardened multi-tenant production service.

## Known limitations

- The contribution count is read from the public GitHub profile page and may be unavailable if GitHub changes its HTML.
- Detected technologies are inferred from language metadata in a limited set of public repositories; they do not represent a complete or verified skills inventory.
- GitHub API rate limits and network availability can interrupt collection.
- ML scores depend on the available dataset and the heuristic target described above.
- The repository does not include a pre-populated database or trained model. Both are generated locally through application use.

## Future improvements

- Add automated unit and integration test coverage for edge cases and security-sensitive flows.
- Introduce CSRF protection and login rate limiting.
- Improve GitHub API retry/backoff and collection observability.
- Add data-retention controls and clearer provenance for each derived skill.
- Rework ML evaluation around independent, reviewed labels and a larger representative dataset.
- Improve deployment configuration and add a documented production WSGI setup.

## License

No open-source license has been selected for this repository yet. Add a `LICENSE` file before inviting others to reuse, modify, or redistribute the code.
