# Phase 4: Authentication and Authorization

> **Status:** ✅ Complete (22/22 tests passing)

This document describes the user authentication and authorization system implemented in Phase 4, including JWT tokens, password hashing, and multi-tenant job isolation.

## Overview

Phase 4 implements a complete authentication and authorization system for the distributed job processing platform. Users must register and authenticate to access job processing APIs. All job operations are isolated by user to prevent cross-tenant data access.

**Key Features:**
- User registration and login endpoints
- JWT-based stateless authentication with HS256 algorithm
- Argon2 password hashing (production-grade, no byte limitations)
- Protected job endpoints with Bearer token validation
- Multi-tenant job isolation (users see only their own jobs)
- Comprehensive test coverage (8 auth tests + 8 updated job tests)

## Architecture

### Authentication Flow

```
Client                              FastAPI API                         Database
  |                                      |                                 |
  +------- POST /auth/register --------> |                                 |
  |  (email, password, full_name)         |---- store User ------> PostgreSQL
  |  <------- UserResponse (201) -----<   |                                 |
  |                                       |                                 |
  +------- POST /auth/login -----------> |                                 |
  |  (email, password)                    |---- query User -------> PostgreSQL
  |  <------- TokenResponse (200) -----<  | (verify password)               |
  |   (access_token: "eyJ...")            |                                 |
  |                                       |                                 |
  +-- POST /api/v1/jobs -----------> |---- verify token via -------> JWT decode
  |   Authorization: Bearer {token}      |    get_current_user_id           |
  |   (job payload)                       |---- validate ownership --> PostgreSQL
  |  <------- Job (201) -----<            |    (filter by user_id)          |
  |                                       |                                 |
```

### Security Components

1. **Password Hashing**: Argon2 via `passlib` library
   - Uses `CryptContext(schemes=["argon2"], deprecated="auto")`
   - No byte-length limitations (unlike bcrypt's 72-byte limit)
   - Better resistance to GPU brute-force attacks than bcrypt

2. **Token Generation**: JWT (JSON Web Tokens) via `python-jose`
   - Algorithm: HS256 (HMAC with SHA-256)
   - Payload includes `{"sub": str(user_id), "exp": expiration_timestamp}`
   - Expiration: 24 hours from token creation
   - Signed with `settings.secret_key` from environment

3. **Token Validation**: Request-based Bearer token extraction
   - Parses `Authorization: Bearer <token>` header
   - Decodes JWT and validates signature and expiration
   - Returns `user_id` for downstream use
   - Returns 401 Unauthorized if missing or invalid

4. **User Isolation**: Foreign key constraint + query filtering
   - `jobs.user_id` has FK constraint to `users.id` with ON DELETE CASCADE
   - All job queries filter by both `Job.id == job_id AND Job.user_id == user_id`
   - Prevents one user from accessing another user's job data

## Database Schema Changes

### Users Table (new in Phase 4)

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Jobs Table (updated in Phase 4)

```sql
ALTER TABLE jobs ADD COLUMN user_id INTEGER;
ALTER TABLE jobs ADD CONSTRAINT fk_jobs_users 
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

The `user_id` column is nullable to support legacy jobs created before user isolation was implemented. New jobs must have a valid `user_id` set during creation.

## API Endpoints

### Registration

**POST /api/v1/auth/register**

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"  // optional
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

**Error Cases:**
- `409 Conflict`: Email already registered
- `422 Unprocessable Entity`: Password too short (min 8 chars) or invalid email format

### Login

**POST /api/v1/auth/login**

Authenticate with email and password to obtain JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Cases:**
- `401 Unauthorized`: Invalid email or password
- `401 Unauthorized`: User account is inactive (is_active=false)

### Protected Job Endpoints

All job endpoints require the `Authorization: Bearer {token}` header.

**Example: Create Job**

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"name": "process-report", "payload": {"task": "generate"}}'
```

**Job Endpoints Protected:**
- `POST /api/v1/jobs` - Create job (sets user_id from token)
- `GET /api/v1/jobs` - List jobs (filtered to user's jobs only)
- `GET /api/v1/jobs/{job_id}` - Get single job (validates ownership)
- `PATCH /api/v1/jobs/{job_id}/status` - Update status (validates ownership)
- `PATCH /api/v1/jobs/{job_id}/result` - Update result (validates ownership)

## Implementation Details

### Core Security Module

**File: `backend/app/core/security.py`**

```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a password using argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, password_hash)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            return None
        return {"user_id": user_id}
    except JWTError:
        return None

async def get_current_user_id(request: Request) -> int:
    """Dependency to extract user_id from Bearer token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = parts[1]
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    return payload["user_id"]
```

### Authentication Routes

**File: `backend/app/api/v1/routes/auth.py`**

```python
from fastapi import APIRouter, HTTPException
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.db.models import User
from app.db.session import SessionLocal

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(user: UserRegister):
    """Register a new user."""
    db = SessionLocal()
    try:
        # Check if email already exists
        existing = db.query(User).filter(User.email == user.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="User with this email already exists")
        
        # Create new user with hashed password
        db_user = User(
            email=user.email,
            password_hash=hash_password(user.password),
            full_name=user.full_name
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    finally:
        db.close()

@router.post("/login", response_model=TokenResponse)
def login_user(credentials: UserLogin):
    """Login user and return JWT token."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User account is inactive")
        
        # Generate JWT token
        token = create_access_token({"sub": str(user.id)})
        
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()
```

### Protected Job Endpoints

**File: `backend/app/api/v1/routes/jobs.py` (updated)**

```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user_id
from app.db.models import Job
from app.db.session import SessionLocal

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse, status_code=201)
def create_job(
    job: JobCreate,
    user_id: int = Depends(get_current_user_id)
):
    """Create a new job for the authenticated user."""
    db = SessionLocal()
    try:
        db_job = Job(
            name=job.name,
            payload=json.dumps(job.payload) if job.payload else None,
            user_id=user_id  # Set user_id from authenticated context
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    finally:
        db.close()

@router.get("", response_model=list[JobResponse])
def list_jobs(user_id: int = Depends(get_current_user_id)):
    """List jobs for the authenticated user."""
    db = SessionLocal()
    try:
        jobs = db.query(Job).filter(Job.user_id == user_id).all()
        return jobs
    finally:
        db.close()

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, user_id: int = Depends(get_current_user_id)):
    """Get a specific job (validate ownership)."""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == user_id
        ).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
    finally:
        db.close()
```

## Testing Strategy

### Unit Tests

**File: `backend/tests/test_auth_api.py`** (8 tests)

- ✅ `test_register_user_creates_account` - User registration with password hashing validation
- ✅ `test_register_duplicate_email_fails` - Duplicate email prevention (409 Conflict)
- ✅ `test_login_with_valid_credentials` - Token generation with valid credentials
- ✅ `test_login_with_invalid_password` - Invalid password rejection (401 Unauthorized)
- ✅ `test_login_with_nonexistent_email` - Non-existent user rejection (401 Unauthorized)
- ✅ `test_protected_job_endpoint_requires_token` - Missing token rejection (401 Unauthorized)
- ✅ `test_create_job_with_valid_token` - Job creation with valid authentication
- ✅ `test_list_jobs_only_shows_user_jobs` - Multi-tenant isolation validation

### Integration Tests

**File: `backend/tests/test_jobs_api.py`** (8 updated tests)

All job API tests updated to use JWT authentication:
- ✅ `test_create_job_returns_created_record` - Authenticated job creation
- ✅ `test_list_jobs_returns_created_jobs` - Authenticated job listing
- ✅ `test_get_job_by_id_returns_single_job` - Authenticated single job retrieval
- ✅ `test_update_job_status_transitions_to_running` - Authenticated status update
- ✅ `test_update_job_status_rejects_invalid_status` - Validation with auth
- ✅ `test_complete_job_marks_finished_at` - Authenticated job completion
- ✅ `test_cancel_job_marks_cancelled_status` - Authenticated job cancellation
- ✅ `test_update_job_result_sets_completion_output` - Authenticated result update

### Test Database Isolation

Tests use unique email addresses to prevent database pollution:

```python
import uuid

def _unique_email() -> str:
    """Generate a unique email for testing."""
    return f"user-{uuid.uuid4().hex[:8]}@example.com"
```

This approach ensures each test uses a fresh email address, avoiding conflicts from previous test runs.

## Security Considerations

### Production Configuration

Before deploying to production:

1. **Change the secret key:**
   ```python
   # .env
   SECRET_KEY=<generate-a-strong-random-key>
   ```
   
   Generate a strong key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use HTTPS only** - All authentication requests must use HTTPS to protect tokens in transit.

3. **Set secure cookie flags** - If using cookies instead of headers.

4. **Implement rate limiting** - Prevent brute-force attacks on login/register endpoints.

5. **Add CORS configuration** - Restrict API access to trusted frontend origins.

6. **Monitor suspicious activity** - Track failed login attempts and unusual patterns.

### Password Requirements

- Minimum 8 characters (enforced in `UserRegister` schema)
- No maximum length (unlike bcrypt)
- Consider adding complexity requirements (uppercase, numbers, special chars) in production

### Token Security

- Tokens expire after 24 hours - users must re-login to get new tokens
- Tokens are stateless - no server-side token revocation without additional infrastructure
- Consider adding token blacklist/refresh tokens in production for logout support

### Data Access Control

- All job operations check both resource ID and user_id
- Foreign key constraints prevent orphaned job records
- ON DELETE CASCADE ensures data consistency when users are deleted

## Migration from Legacy Data

Phase 4 created the `users` table and added `user_id` to `jobs`. Existing jobs have `NULL` user_id values.

**To migrate legacy data to a system user:**

```sql
INSERT INTO users (email, password_hash, full_name, is_active) 
VALUES ('system@internal', '<hashed_password>', 'System User', false);

UPDATE jobs SET user_id = (SELECT id FROM users WHERE email = 'system@internal') 
WHERE user_id IS NULL;
```

Then make `user_id` NOT NULL in future migrations once legacy data is handled.

## Next Phases

Phase 5 will introduce Redis for job queuing, enabling async job processing with worker threads/processes. Phase 6 will integrate Celery for distributed task execution. Both phases will inherit the multi-tenant isolation and authentication already implemented in Phase 4.

## Dependencies

Phase 4 added the following production dependencies:

- `python-jose[cryptography]>=3.3,<4.0` - JWT token handling
- `passlib[argon2]>=1.7,<2.0` - Password hashing with argon2
- `argon2-cffi>=23.1.0` - Argon2 implementation (installed as dependency of passlib)

Run `pip install -r backend/requirements.txt` to install all dependencies.

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT specification and token debugger
- [Argon2 Password Hashing](https://argon2-cffi.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
