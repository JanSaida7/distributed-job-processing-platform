# Distributed Job Processing Platform

A production-oriented portfolio project for learning how to design and operate a distributed job processing system. The platform will accept jobs through a versioned REST API, track their lifecycle, and process them asynchronously with workers.

> **Current status:** Phase 0 complete. Repository and development environment initialized. Application features are planned.

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

This architecture is planned. Its components will be introduced phase by phase and are not implemented yet.

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
2. FastAPI backend foundation: **Planned**
3. PostgreSQL database: **Planned**
4. Job model and REST APIs: **Planned**
5. Authentication and authorization: **Planned**
6. Redis: **Planned**
7. Celery workers: **Planned**
8. Retry mechanism and failure handling: **Planned**
9. Dead Letter Queue: **Planned**
10. Idempotency and concurrency safety: **Planned**
11. Basic React frontend: **Planned**
12. Docker and Docker Compose: **Planned**
13. Testing and code quality: **Planned**
14. AWS deployment: **Planned**
15. CloudWatch monitoring and logging: **Planned**
16. GitHub Actions CI/CD: **Planned**
17. Scaling and performance testing: **Planned**
18. Final documentation and resume preparation: **Planned**

## Project Structure

```text
backend/                  # Backend application, added in later phases
frontend/                 # React application, added in a later phase
docs/architecture/        # Architecture decisions and diagrams
docs/api/                 # API documentation, added with API endpoints
docs/development/         # Local development and contribution guidance
.github/workflows/        # CI workflows, added in the CI/CD phase
```

## Local Development

Phase 0 requires only Python and Git. No packages or services are required yet.

```powershell
python --version
git --version
git status
git remote -v
```

Application setup instructions will be added as each phase introduces a runnable component.

## Environment Variables

`.env.example` contains placeholder configuration names for planned phases. Copy it to `.env` only for local development when configuration is required. Never commit `.env` or real credentials.

## Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Development guide](docs/development/development-guide.md)

API documentation will be added when the first endpoint is implemented.

## Testing

Automated tests are planned and will be introduced with the first application code. The project will use Pytest and tests will be run before meaningful commits.

## Future Improvements

Scaling, richer job types, production deployment, monitoring, CI/CD, and frontend workflows are planned for later phases. They are intentionally not implemented in Phase 0.
