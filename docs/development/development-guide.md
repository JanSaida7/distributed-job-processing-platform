# Development Guide

## Prerequisites

Phase 0 requires:

- Git
- Python 3.13 or a compatible supported Python version
- VS Code or another editor
- A GitHub account with access to the repository

No Python packages or external services are required yet.

## Git Workflow

1. Start from an up-to-date `main` branch.
2. Create a focused branch for each change.
3. Keep commits small and related to one meaningful activity.
4. Run the relevant tests and checks before committing.
5. Review `git diff` and `git status` before requesting review.
6. Push only when explicitly intended, and open a pull request for review.

Never commit `.env`, credentials, tokens, private keys, or other secrets.

## Branch Naming Convention

Use lowercase names with a category and short description:

- `feat/fastapi-foundation`
- `fix/job-status-transition`
- `test/job-api`
- `docs/architecture-overview`
- `chore/project-structure`
- `ci/test-workflow`

## Local Development Principles

- Follow the existing project structure and introduce directories when their phase requires them.
- Prefer readable, focused functions with type hints.
- Use environment variables for configuration; never hardcode secrets.
- Validate inputs at API boundaries and return appropriate HTTP status codes.
- Keep error responses consistent and avoid exposing internal exceptions.
- Document architectural decisions, especially why a new component is needed.
- Do not add future-phase technologies early without a concrete dependency.

## Frontend Development

Phase 9 adds a React and Vite dashboard in `frontend/`. Run `npm install` once, then `npm run dev` from that directory. The default API address is `http://127.0.0.1:8000`; override it with `VITE_API_BASE_URL` in a local frontend environment file. Ensure the frontend origin is present in the backend `CORS_ORIGINS` setting.

## Testing Principles

- Add tests with each behavior change.
- Test important success paths, validation failures, authorization failures, and error handling.
- Keep tests deterministic and independent of external services where possible.
- Run the smallest relevant test set during development, then the full suite before a meaningful commit.
- Pytest will be the project test framework once application code is introduced.

## Quality Checks

Phase 11 makes backend tests self-contained through an in-memory SQLite test database, preventing test runs from changing a local PostgreSQL instance or enqueueing real jobs. Run `pytest` and `ruff check app` from `backend/`. Run `npm run test`, `npm run lint`, and `npm run build` from `frontend/` for the dashboard checks.

## Commit Conventions

Use imperative, descriptive Conventional Commit messages:

- `feat: add job creation endpoint`
- `fix: reject invalid job transition`
- `test: cover authentication failures`
- `docs: explain queue architecture`
- `chore: initialize project structure`
- `ci: add test workflow`

A commit should explain one coherent change. Avoid vague messages such as `update`, `changes`, or `fix stuff`.
