# Architecture Overview

## Status

This document describes the architecture through Phase 9. FastAPI, PostgreSQL, Redis/Celery, authentication, and the React dashboard are implemented locally. Containerization and cloud infrastructure remain planned.

## Current Application Boundary

FastAPI provides the HTTP boundary, validates requests and responses through Pydantic, exposes versioned routes under `/api/v1`, and reads settings from environment variables. SQLAlchemy manages PostgreSQL sessions and Alembic controls schema changes. The API has `users` and `jobs` tables, JWT authentication, user-scoped job access, and configurable CORS for the dashboard.

PostgreSQL is used for durable, relational state. SQLAlchemy provides a consistent Python session interface, while Alembic records schema changes as versioned migrations. Keeping these concerns separate from route handlers makes later user and job features easier to test and evolve.

API versioning keeps the public contract explicit. Future breaking changes can be introduced under another version while existing clients continue using the current version.

## Intended System

Clients submit and inspect jobs through the versioned FastAPI REST API. The API persists job state in PostgreSQL and hands work to Celery through Redis so that the request remains short.

Redis is the queue transport and Celery workers consume queued jobs, execute supported payload operations, and update job state. PostgreSQL remains the source of truth for users, jobs, lifecycle state, retry information, and timestamps.

The React dashboard calls the REST API, supports registration/login, job submission, status polling, job details, retry, cancellation, and failed/dead-letter views. Nginx or a cloud API gateway may sit at the edge in a deployed environment.

## Planned Flow

```text
Client
  |
  v
React dashboard or API consumer
  |
  v
Nginx / API Gateway
  |
  v
FastAPI API
  | \
  |  +--> PostgreSQL: durable users and job state
  |
  +-----> Redis: queue transport and transient coordination
             |
             v
       Celery workers
             |
             v
       Job execution
             |
             +--> PostgreSQL: completed or failed state
             +--> Retry, then Dead Letter Queue after the limit
```

## Planned Infrastructure

The cloud deployment may use ECS or EC2 for application and worker processes, RDS for PostgreSQL, ElastiCache for Redis, S3 for job-related files, ECR for container images, IAM for permissions, and CloudWatch for logs and monitoring. Docker and GitHub Actions are planned to make local execution and delivery repeatable.

These choices are architectural targets, not currently deployed resources.

## Design Principles

- Keep PostgreSQL as the durable source of truth.
- Keep API requests short and delegate long work to workers.
- Validate job state transitions rather than allowing arbitrary updates.
- Make retries explicit and bounded.
- Isolate permanently failing jobs in a dead-letter path.
- Keep secrets in environment configuration and cloud secret management.
- Introduce each component only when its phase requires it.
