# ACEest Fitness — DevOps Assignment

Web version of the **ACEest Fitness & Performance** desktop app (`tkinter` + SQLite). This repository delivers a **Flask** application with **pytest** automation, a **multi-stage Docker** image, and **GitHub Actions** CI.

---

## Table of contents

1. [What this project contains](#what-this-project-contains)
2. [Repository layout](#repository-layout)
3. [Prerequisites](#prerequisites)
4. [Step-by-step: local development](#step-by-step-local-development)
5. [Running the application](#running-the-application)
6. [Automated tests (pytest)](#automated-tests-pytest)
7. [Docker](#docker)
8. [Continuous integration (GitHub Actions)](#continuous-integration-github-actions)
9. [Suggested Git workflow (branches and pull requests)](#suggested-git-workflow-branches-and-pull-requests)
10. [Security and configuration notes](#security-and-configuration-notes)
11. [Troubleshooting](#troubleshooting)

---

## What this project contains

| Area | Description |
|------|-------------|
| **Web app** | Flask app factory (`aceest`), session login (default `admin` / `admin`), client list and add, “current client” in session, client summary page. |
| **Data** | SQLite file `aceest_fitness.db` (gitignored); schema matches the original desktop app. |
| **Tests** | `pytest` suite under `tests/` with isolated temp databases via `conftest.py`. |
| **Container** | Production-oriented image: **Gunicorn**, non-root user, health check on `/health`. |
| **CI** | Workflow builds the app (byte-compile), builds the **runtime** Docker image, and runs **pytest inside** the **`ci-test`** Docker stage. |

---

## Repository layout

```text
aceest/                 # Application package
  __init__.py           # create_app(), DB init, blueprint registration
  auth.py               # login_required, client_required, safe_next_url
  db.py                 # SQLite schema, init_db(), get_db(), close_db()
  routes.py             # HTTP routes (login, clients, summary, health, …)
  templates/            # Jinja2 HTML templates
tests/                  # Pytest tests
  conftest.py           # App + client fixtures; temp DB path
  test_auth.py
  test_routes.py
wsgi.py                 # WSGI entry: app = create_app()
requirements.txt        # Runtime deps (Flask, matplotlib, fpdf2 — for parity / future features)
requirements-dev.txt    # Extends requirements.txt + pytest
requirements-docker.txt # Minimal prod image: Flask + gunicorn only
Dockerfile              # builder → ci-test → runtime stages
.dockerignore           # Smaller/safer build context
.github/workflows/ci.yml
pytest.ini
.gitignore
```

The original desktop script (e.g. `Aceestver-3.2.4.py`) is **not required** for the web app to run; add it to the repo only if you want it as reference material.

---

## Prerequisites

- **Python 3.12** (aligned with CI and Docker `PYTHON_VERSION`)
- **Git**
- **Docker** (optional, for container build/run)
- **GitHub account** (for Actions and PRs)

---

## Step-by-step: local development

### 1. Clone the repository

```bash
git clone https://github.com/<your-user>/DevOps-Assignment.git
cd DevOps-Assignment
```

### 2. Create and activate a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

For **tests** locally, also install dev requirements:

```bash
pip install -r requirements-dev.txt
```

### 4. Run the application (see next section)

On first run, `init_db()` creates `aceest_fitness.db` and seeds the default admin user.

---

## Running the application

### Development server (Flask)

From the repository root, with the virtual environment active:

```bash
# Windows PowerShell example
$env:SECRET_KEY = "dev-secret-change-me"
flask --app wsgi run
```

Then open **http://127.0.0.1:5000/** in a browser.

- **Health (JSON):** `GET http://127.0.0.1:5000/health`
- **Default login:** `admin` / `admin` (change or extend users in the database for real use).

### Production-style server (Gunicorn, local)

After `pip install gunicorn` (or using dependencies from `requirements-docker.txt` in a venv):

```bash
gunicorn --bind 127.0.0.1:8000 wsgi:app
```

---

## Automated tests (pytest)

Install dev dependencies, then run from the **repository root**:

```bash
pytest
```

What the suite covers (high level):

- `GET /health` JSON response
- Login success and failure, dashboard protection
- Client add/list, duplicate handling, session “current client”, summary redirect rules, logout

Tests use a **temporary SQLite file** per test session (see `tests/conftest.py`), so they do not touch your real `aceest_fitness.db`.

---

## Docker

### Why multiple requirement files?

- **`requirements-docker.txt`** — Used by the **production** image stage: **Flask + Gunicorn** only → **smaller** image. When you add chart/PDF **routes** that need `matplotlib` / `fpdf2`, add those packages here (or switch the Dockerfile to install `requirements.txt`).
- **`requirements.txt`** — Full stack for local dev and parity with the original desktop dependencies.

### Dockerfile stages

| Stage | Purpose |
|--------|---------|
| **builder** | Creates a virtualenv and installs `requirements-docker.txt` for the slim runtime image. |
| **ci-test** | Installs `requirements.txt` + `requirements-dev.txt`, copies the app and `tests/`, runs **`pytest -q`**. Used by CI to test **inside a container**. |
| **runtime** (default) | Minimal image: copies the venv from **builder** plus `wsgi.py` and `aceest/`. Runs **Gunicorn** as a non-root user; **HEALTHCHECK** calls `/health`. |

Default `docker build .` builds the **`runtime`** stage (last stage in the Dockerfile).

### Build and run the production image

```bash
docker build -t aceest:local .
docker run --rm -p 8000:8000 -e SECRET_KEY="use-a-long-random-secret" aceest:local
```

Open **http://localhost:8000/**.

For **persistent** SQLite data, mount a volume on `/app` (where the process writes `aceest_fitness.db` by default), for example:

```bash
docker run --rm -p 8000:8000 -e SECRET_KEY="..." -v aceest-data:/app aceest:local
```

### Build the CI test stage locally

```bash
docker build --target ci-test -t aceest:ci-test .
```

This fails the build if any test fails.

---

## Continuous integration (GitHub Actions)

Workflow file: **`.github/workflows/ci.yml`**

**Triggers:** `push` and `pull_request` to **`main`** or **`master`**.

**Jobs:**

1. **Build & lint (compile)**  
   - Checkout  
   - Setup **Python 3.12** with pip cache  
   - `pip install -r requirements.txt -r requirements-dev.txt`  
   - `python -m compileall -q aceest wsgi.py tests` → syntax errors fail the workflow  

2. **Docker image (production)**  
   - Runs after job (1) succeeds  
   - **Docker Buildx** + `docker/build-push-action`  
   - Builds Dockerfile **`target: runtime`** (image is **not** pushed; validates the production Dockerfile)  
   - Uses **GitHub Actions cache** for layers  

3. **Pytest in container (ci-test stage)**  
   - Runs after job (1) succeeds (in parallel with job (2))  
   - Builds **`target: ci-test`**, which executes **`RUN pytest -q`** during the image build  

**Concurrency:** New runs on the same branch cancel older in-progress runs for the same workflow.

**Permissions:** `contents: read` (minimal for checkout and cache usage).

After merging to `main`, open the repository on GitHub → **Actions** to see run history and logs.

---

## Suggested Git workflow (branches and pull requests)

This assignment is designed around **small, reviewable changes**. A practical sequence:

1. **`main`** stays **deployable**; do feature work on branches.
2. For each feature or chore, create a branch from up-to-date `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/short-description
   ```
3. Commit in **small batches** with clear messages (e.g. `feat: …`, `test: …`, `chore: …`, `ci: …`, `docs: …`).
4. **Push** the branch and open a **Pull Request** into `main`.
5. Wait for **GitHub Actions** to pass (green checks) before merging.
6. Merge via GitHub (merge commit or squash, per course instructions).
7. Locally update `main` after merge:
   ```bash
   git checkout main
   git pull origin main
   ```

Example branch names used in this project (illustrative):

- `feature/flask-env-setup` — dependencies and `.gitignore`
- `feature/...` — Flask login, clients, summary, pytest, Docker, CI

---

## Security and configuration notes

- **SECRET_KEY** — Flask sessions require a strong secret in any real deployment. Set `SECRET_KEY` in the environment (local, Docker `-e`, or your hosting provider). The code falls back to a **development** default if unset.
- **Do not commit** `.env`, database files, or virtualenvs (see `.gitignore`).
- **Docker image** runs as a **non-root** user; expose only the HTTP port you need and put **TLS** in front (reverse proxy or platform ingress).
- **`safe_next_url`** prevents open redirects after login (`//evil.com` is rejected).

---

## Troubleshooting

| Issue | What to check |
|--------|----------------|
| `ModuleNotFoundError` | Virtualenv activated? Ran `pip install -r requirements.txt` from repo root? |
| Tests fail locally | Use `pytest -v` for details; ensure you did not delete `tests/` or `pytest.ini`. |
| Docker build fails on `ci-test` | Same as failing `pytest`; fix tests or app code. |
| Docker `runtime` build OK but app errors | Pass `SECRET_KEY`; check logs: `docker logs <container>`. |
| CI fails on PRs from forks | Caching or token permissions can differ; check the Actions log for the exact step. |
| SQLite “database is locked” | Avoid many writers on one file; in Docker, single container is usually fine. |

---

## License / course use

Use and modify per your **course** or **organization** requirements. Replace placeholder URLs and user names in this README with your own where applicable.
