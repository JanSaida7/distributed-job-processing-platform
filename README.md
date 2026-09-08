# Distributed Job Processing Platform

A production-oriented portfolio project for learning how to design and operate a distributed job processing system. The platform will accept jobs through a versioned REST API, track their lifecycle, and process them asynchronously with workers.

> **Current status:** Phase 9 complete. The platform includes authenticated job APIs, Redis/Celery queue execution, failure handling, retry and cancellation flows, idempotency and optimistic locking, plus a React dashboard for submitting and monitoring jobs.

## Problem Statement

Long-running or resource-intensive tasks should not block an API request. A reliable job processing platform needs to accept work, persist its state, process it asynchronously, handle failures, and expose progress to clients.

## Goals

- Build a readable, maintainable backend with FastAPI.
- Learn the architectural role of PostgreSQL, Redis, queues, and workers.
- Design reliable job lifecycle, retry, dead-letter, and idempotency behavior.
- Practice authentication, testing, containerization, cloud deployment, and monitoring.
- Keep the system simple enough to understand and explain.

## Planned Architecture

```text
Client / React
      |
      v
FastAPI REST API
      |
      +--> PostgreSQL (job and user state)
      +--> Redis (queue and transient state)
      |
      v
Celery Workers --> Job Execution --> Completed / Failed / Dead Letter
```

This architecture is now active for the job-processing pipeline: PostgreSQL stores job state, Redis provides the broker, and Celery workers process queued jobs asynchronously.

## Planned Technology Stack

- Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- PostgreSQL
- JWT authentication and password hashing
- Redis and Celery
- Pytest
- Docker and Docker Compose
- Nginx
- React and Vite
- AWS services including ECS or EC2, RDS, ElastiCache, S3, CloudWatch, ECR, IAM
- GitHub Actions and Vercel

## Development Phases

1. Repository and development environment: **Complete**
2. FastAPI backend foundation: **Complete**
3. PostgreSQL database: **Complete**
4. Job model and REST APIs: **Complete**
5. Authentication and authorization: **Complete**
6. Redis, Celery, retry, failure handling, and reliability hardening: **Complete**
7. Dead-letter and operational queue visibility: **Complete**
8. Idempotency and concurrency safety: **Complete**
9. Basic React frontend: **Complete**
10. Docker and Docker Compose: **Planned**
11. Testing and code quality: **Planned**
12. AWS deployment: **Planned**
13. CloudWatch monitoring and logging: **Planned**
14. GitHub Actions CI/CD: **Planned**
15. Scaling and performance testing: **Planned**
16. Final documentation and resume preparation: **Planned**

## Project Structure

```text
backend/                  # FastAPI backend foundation
frontend/                 # React/Vite dashboard for job submission and monitoring
docs/architecture/        # Architecture decisions and diagrams
docs/api/                 # API documentation, added with API endpoints
docs/development/         # Local development and contribution guidance
.github/workflows/        # CI workflows, added in the CI/CD phase
```

## Local Development

### Backend setup

From the repository root, create a virtual environment, activate it, and install the backend dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

Start the API from the `backend` directory:

```powershell
Set-Location backend
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Interactive API documentation is available at `/docs`.

### Frontend setup

In a second terminal, start the React dashboard:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dashboard connects to `http://127.0.0.1:8000` by default. Set `VITE_API_BASE_URL` in `frontend/.env.local` to use another API address.

Run the backend tests from the `backend` directory:

```powershell
pytest
```

```powershell
python --version
git --version
git status
git remote -v
```

The API requires PostgreSQL. Redis and a Celery worker are required to process queued jobs asynchronously; without them, the API remains available but newly submitted jobs cannot be processed.

### PostgreSQL database

The application uses a local PostgreSQL database named `job_processing`. Set `DATABASE_URL` in the root `.env` file; keep the password local and never commit `.env`.

From the `backend` directory, the database migration commands are:

```powershell
alembic upgrade head
```

Migrations create the `users` and `jobs` tables, including job idempotency and version fields.

## Environment Variables

`.env.example` documents the backend configuration. Copy it to `.env` for local development and never commit real credentials.

## Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Development guide](docs/development/development-guide.md)

See the [API endpoint documentation](docs/api/endpoints.md) for the currently available endpoints.

## Testing

The backend uses Pytest. Run `pytest` from `backend/` before meaningful commits.

## Future Improvements

Scaling, richer job types, production deployment, monitoring, and CI/CD are planned for later phases.
