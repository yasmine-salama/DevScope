# DevScope
### GitHub Developer Profile Analytics Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy"/>
  <img src="https://img.shields.io/badge/Scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white" alt="Scikit-learn"/>
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly"/>
</p>

<p align="center">
  <strong>Collect. Process. Analyze. Discover.</strong>
</p>

---

## Overview

**DevScope** is a Flask-based web application designed to collect, organize, explore, and compare public GitHub developer profiles.

The application combines an ETL workflow, relational database management, interactive analytics, profile search, data exports, and experimental machine-learning-assisted job matching.

It transforms publicly available GitHub information into structured data and analytical insights through an integrated web interface.

Developed as an academic project, DevScope brings together practical concepts from **Data Engineering, Data Analysis, and Machine Learning**.

## Features

### 01. Authentication & User Management

- User registration, login, and logout.
- Secure password hashing.
- User-specific profile collections and favorites.
- Search history and profile operation tracking.
- Access control for profiles associated with each user's workspace.

### 02. GitHub Data Collection

Collect public developer information using the GitHub REST API.

The application retrieves information such as:

- GitHub username and display name.
- Biography and location.
- Profile URL and avatar.
- Followers and public repository count.
- Public repository information.
- Repository language metadata.
- Available contribution and activity information.

A GitHub Personal Access Token can optionally be configured to benefit from higher API rate limits.

### 03. ETL Pipeline

DevScope implements an Extract, Transform, Load workflow to process GitHub developer data.

| Stage | Operations |
|---|---|
| **Extract** | Search GitHub users and retrieve public profile and repository information. |
| **Transform** | Normalize fields, handle missing values, remove duplicate profiles, and derive technology and activity indicators. |
| **Load** | Create or update developer records and associate collected profiles with the requesting user. |

The pipeline also records execution information, including processing counts, statuses, and logs.

### 04. Interactive Dashboard & Analytics

The dashboard provides an overview of collected developer data through:

- Key Performance Indicators (KPIs).
- Collected profile statistics.
- Technology distribution.
- Developer activity indicators.
- Location and platform information.
- Profile growth and other analytical indicators.
- Recent collection and activity summaries.

Interactive visualizations help users explore and interpret the collected information.

### 05. Developer Search & Profile Management

- Search profiles by username, display name, or location.
- Filter by technology, platform, activity, date range, repository count, and followers.
- Sort and paginate search results.
- View developer details and detected technologies.
- Save profiles to Favorites.
- Update or remove profiles from a personal workspace.
- Review profile operations.

### 06. Profile Comparison & Job Matching

The application provides profile comparison and an experimental job-matching module.

Users can specify:
- A job title.
- Required technologies.
- Required skills.
- An experience level.

The matching process combines:
- Required-skill overlap.
- An experimental machine-learning model score.
- An experience-related score.

The results provide a ranked list of developer profiles based on these indicators.

### 07. Data Export

Export dashboard and developer information in different formats:

| Format | Purpose |
|---|---|
| CSV | Export tabular information. |
| Excel (.xlsx) | Export structured data for further analysis. |
| PDF | Generate dashboard and individual developer reports. |

### 08. Administration

A read-only administration area provides monitoring information about:

- Registered users.
- Collected developer profiles.
- Technologies.
- ETL executions and logs.
- General application statistics.

Administrative access is controlled through the user's `is_admin` database field.

---

## Technology Stack

| Category | Technologies |
|---|---|
| **Programming Language** | Python |
| **Backend Framework** | Flask |
| **ORM & Database Integration** | Flask-SQLAlchemy, SQLAlchemy |
| **Frontend** | HTML, CSS, JavaScript, Jinja |
| **Data Processing** | Pandas, NumPy |
| **Data Collection** | GitHub REST API, Requests, BeautifulSoup |
| **Database** | SQLite, MySQL |
| **Data Visualization** | Plotly, Matplotlib |
| **Machine Learning** | Scikit-learn |
| **ML Techniques** | TF-IDF, Logistic Regression, K-Nearest Neighbors, Random Forest |
| **Data Export** | OpenPyXL, ReportLab |
| **Model Persistence** | Joblib |

---

## Application Architecture

DevScope follows a modular architecture that separates application routes, business logic, data processing, and persistence.

```mermaid
flowchart TD
    A["User / Browser"] --> B["Flask Routes & Jinja Templates"]
    B --> C["Application Services"]

    C --> D["GitHub ETL Pipeline"]
    D --> E["GitHub REST API"]
    D --> F["Public GitHub Profile Pages"]

    C --> G["SQLAlchemy ORM"]
    G --> H[("SQLite / MySQL Database")]

    C --> I["Analytics Services"]
    C --> J["Export Services"]
    C --> K["ML Feature Engineering & Matching"]

    I --> B
    J --> B
    K --> B
```

### Main Application Modules

| Module | Responsibility |
|---|---|
| `etl/` | GitHub data collection and ETL pipeline orchestration. |
| `ml/` | Feature engineering, model training, prediction, and profile matching. |
| `models/` | Database models and relationships. |
| `routes/` | Authentication, application pages, API endpoints, and administration. |
| `services/` | Analytics, search, exports, authentication, and profile management. |
| `templates/` | HTML pages rendered with Jinja. |
| `static/` | CSS, JavaScript, and interface icons. |

---

## Machine Learning Approach

The machine-learning component explores developer-profile classification and job matching.

### Classification Models

The training module experiments with three classifiers:

- Logistic Regression
- K-Nearest Neighbors (KNN)
- Random Forest

### Feature Engineering

The feature pipeline combines numerical profile indicators, including:

- Followers.
- Public repositories.
- Contributions.
- Account age.
- Recent activity.
- Detected technology count.

It also uses TF-IDF features derived from repository languages and detected skills.

### Important Methodological Limitation

The current training process generates its `high_quality` target using a percentile threshold over the application's own weighted `global_score`.

Since this score is itself calculated from profile indicators used by the model, the ML component is an experimental approximation of an internal scoring rule.

It is **not trained on independently labelled recruitment outcomes or verified developer-quality data**.

Therefore, its metrics and matching scores should be interpreted as exploratory decision-support indicators, not as proof of recruitment accuracy or an automated hiring decision.

---

## Project Structure

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
│   │
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
│
├── .gitignore
└── README.md
```

---

## Getting Started

### Requirements

- Python 3.11 (recommended).
- Git.
- Internet connection for GitHub data collection.
- GitHub Personal Access Token (optional).

The default database is SQLite, so a separate database server is not required for local execution.

### 1. Clone the Repository

```bash
git clone https://github.com/yasmine-salama/DevScope.git
cd DevScope
```

### 2. Navigate to the Backend

```bash
cd backend
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS / Linux:

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a local `.env` file from the provided example.

**Windows (PowerShell):**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Open `.env` and configure the required settings:

```dotenv
SECRET_KEY=your_generated_secret_key
DATABASE_URL=sqlite:///devscope.db
GITHUB_TOKEN=
SESSION_COOKIE_SECURE=false
```

Generate a secure secret key using:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

| Variable | Description |
|---|---|
| `SECRET_KEY` | Required secret used to sign Flask sessions. Must contain at least 32 characters. |
| `DATABASE_URL` | Database connection URL. Defaults to SQLite. |
| `GITHUB_TOKEN` | Optional GitHub token for authenticated API requests. |
| `SESSION_COOKIE_SECURE` | Enable secure session cookies when serving the application over HTTPS. |

For MySQL, configure a SQLAlchemy connection URL:

```dotenv
DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DATABASE_NAME
```

**Security:** Never commit your `.env` file, GitHub token, passwords, or secret keys.

### 6. Run the Application

From inside the `backend/` directory:

```bash
python run.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000
```

The database schema is initialized when the application starts.

The built-in Flask server is intended for local development, not production deployment.

---

## How to Use DevScope

1. Open the application and create a user account.
2. Sign in and access the dashboard.
3. Use GitHub search and collection controls to find public developer profiles.
4. Run an ETL collection with a search query and a suitable profile limit.
5. Explore collected profiles through Search and Developer Details.
6. Save interesting profiles to Favorites.
7. Compare selected developer profiles.
8. Explore the experimental ML model and job-matching functionality.
9. Export dashboard or profile information in CSV, Excel, or PDF format.
10. Review ETL execution history and logs.

GitHub collection depends on network availability and API rate limits. A token is optional, but recommended for repeated collection.

---

## Tests

Functional tests are available in the backend directory.

Run them using:

```bash
python -m unittest discover -s tests -v
```

The tests cover key application flows, including user data isolation, ETL behavior with mocked GitHub responses, ML pages, and export endpoints.

They do not replace a complete security review or production acceptance test.

---

## Known Limitations

- GitHub contribution information is retrieved from public profile pages and may become unavailable if GitHub changes its page structure.
- Detected technologies are inferred from language metadata in a limited set of public repositories; they are not a complete or verified skills inventory.
- GitHub API rate limits and network availability can interrupt data collection.
- ML scores depend on the available dataset and the heuristic target-generation approach.
- The repository does not include a pre-populated database or trained model. These are generated locally through application use.
- The application is an academic/demo project and is not hardened for production multi-tenant deployment.

---

## Future Improvements

- Expand unit and integration test coverage.
- Introduce CSRF protection and login rate limiting.
- Improve GitHub API retry and backoff mechanisms.
- Add data-retention controls and clearer data provenance.
- Improve ML evaluation using independent and reviewed labels.
- Enhance deployment configuration and production WSGI support.

---

## Author

**Yasmine Salama**

Data Science Student | Data Engineering

[GitHub Profile](https://github.com/yasmine-salama)

[DevScope Repository](https://github.com/yasmine-salama/DevScope)

---

<p align="center">
  <strong>DevScope</strong><br/>
  <sub>Collect. Process. Analyze. Discover.</sub>
</p>
