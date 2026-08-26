# Architecture Overview

## Status

This document describes the intended final architecture. The components below are planned and will be introduced incrementally. Phase 0 contains repository scaffolding only.

## Intended System

Clients will submit and inspect jobs through a versioned FastAPI REST API. The API will validate requests and coordinate durable state in PostgreSQL. Long-running work will be handed to a queue instead of being performed during the request.

Redis is planned as the queue transport and for short-lived coordination data. Celery workers will consume queued jobs, execute the supported job types, and update job state. PostgreSQL will remain the source of truth for users, jobs, lifecycle state, retry information, and timestamps.

A future React dashboard will call the REST API and display job lists, status, retry information, and errors. Nginx or a cloud API gateway may sit at the edge in a deployed environment.

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
