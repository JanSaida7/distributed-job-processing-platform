# API Endpoints

## API conventions

The API is versioned under `/api/v1`. Versioning makes the public URL contract explicit and gives future releases room for breaking changes without silently changing existing clients.

Successful responses use the endpoint-specific schema. Errors use this common shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": []
  }
}
```

`/health`, `/info`, `/queue-status`, and `/queue-metrics` are public. Job endpoints require a Bearer JWT obtained from the authentication endpoints.

## Implemented endpoint groups

- `POST /auth/register` and `POST /auth/login` register users and issue JWTs.
- `GET` and `POST /jobs` list and submit the authenticated user's jobs.
- `GET /jobs/{job_id}`, `POST /jobs/{job_id}/cancel`, and `POST /jobs/{job_id}/retry` inspect or control a job.
- `GET /jobs/failed` and `GET /jobs/dead-letter` provide operational views.
- `PATCH /jobs/{job_id}/status` supports version-aware status updates; `PATCH /jobs/{job_id}/result` records a result.

## GET /api/v1/health

Purpose: Confirm that the FastAPI application is running.

Authentication: None.

Request body: None.

Request parameters: None.

Successful response, `200 OK`:

```json
{
  "status": "ok"
}
```

Error responses: No endpoint-specific errors are currently expected.

Example request:

```powershell
curl http://127.0.0.1:8000/api/v1/health
```

## GET /api/v1/info

Purpose: Return basic application information.

Authentication: None.

Request body: None.

Request parameters: None.

Successful response, `200 OK`:

```json
{
  "name": "distributed-job-processing-platform",
  "environment": "development",
  "version": "0.1.0"
}
```

Error responses: No endpoint-specific errors are currently expected.

Example request:

```powershell
curl http://127.0.0.1:8000/api/v1/info
```
