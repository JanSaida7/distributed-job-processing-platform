# API Endpoints

## API conventions

The Phase 1 API is versioned under `/api/v1`. Versioning makes the public URL contract explicit and gives future releases room for breaking changes without silently changing existing clients.

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

No authentication is required in Phase 1. Authentication is planned for a later phase.

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