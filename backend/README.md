# Backend

The backend is a small FastAPI application. Phase 1 provides the versioned health and information endpoints, environment-based configuration, and a basic consistent error response format.

## Setup

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

## Run

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation.

## Test

Run from the `backend` directory:

```powershell
pytest
```

PostgreSQL, Redis, Celery, authentication, and job processing are planned for later phases.