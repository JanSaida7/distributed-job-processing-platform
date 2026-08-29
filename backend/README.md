# Backend

The backend is a FastAPI application with a PostgreSQL database. Phase 1 provides versioned health and information endpoints with environment-based configuration. Phase 2 adds SQLAlchemy sessions and Alembic migrations. Phase 3 implements the complete job lifecycle API with create, read, update, status transitions, and result handling.

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

## Database

Set `DATABASE_URL` in the repository root `.env` file:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_LOCAL_PASSWORD@localhost:5432/job_processing
```

Run migrations from this directory:

```powershell
alembic upgrade head
```

Users and jobs tables are created in Phase 3 with full Alembic migrations.

Redis, Celery, authentication, and distributed job processing are planned for later phases.