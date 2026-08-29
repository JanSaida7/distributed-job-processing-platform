# Alembic migrations

This directory contains database migration scripts. Phase 2 establishes the migration environment; application tables will be added in later phases.

From the `backend` directory, create a migration with:

```powershell
alembic revision -m "describe schema change"
```

Apply migrations with:

```powershell
alembic upgrade head
```