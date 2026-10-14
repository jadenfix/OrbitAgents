"""
OrbitAgents Authentication Service

FastAPI application for user registration, authentication, and JWT management.
"""

import logging
import re
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DatabaseError, IntegrityError
from sqlalchemy.orm import Session

from config import settings
from database import engine, get_db
from models import Base, User
from passwords import password_bytes
from schemas import Token, UserCreate, UserLogin, UserResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="OrbitAgents Auth Service",
    description="Authentication and authorization service for OrbitAgents platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Security middleware - Skip trusted host middleware for testing
# In production, uncomment and configure:
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "127.0.0.1", "*.orbitagents.dev"]
# )

# CORS middleware
try:
    allowed_origins = settings.ALLOWED_ORIGINS.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    logger.info(f"CORS configured with origins: {allowed_origins}")
except Exception as e:
    logger.error(f"Failed to configure CORS: {e}")
    raise

# Matching bcrypt's 12-round cost also for absent users/empty credentials.
# Use direct maintained bcrypt: Passlib's old backend silently truncated >72 bytes.
_DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt(rounds=12))

# JWT Security
security = HTTPBearer(auto_error=False)  # Don't auto-error to handle custom responses

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram("http_request_duration_seconds", "HTTP request duration")
LOGIN_ATTEMPTS = Counter(
    "auth_login_attempts_total", "Total login attempts", ["status"]
)
REGISTRATION_ATTEMPTS = Counter(
    "auth_registration_attempts_total", "Total registration attempts", ["status"]
)

# Rate limiting storage (in production, use Redis)
rate_limit_storage: defaultdict[str, deque[float]] = defaultdict(deque)


def is_rate_limited(
    identifier: str, max_requests: int = 10, window_seconds: int = 300
) -> bool:
    """
    Simple in-memory rate limiting with enhanced logging.

    Args:
        identifier: Unique identifier for rate limiting (e.g., IP address)
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds

    Returns:
        True if rate limited, False otherwise
    """
    # Honor the explicit service configuration; test environment markers do not
    # bypass production policy.
    if not settings.RATE_LIMIT_ENABLED:
        return False

    current_time = time.time()
    requests = rate_limit_storage[identifier]

    # Remove old requests outside the window
    while requests and requests[0] <= current_time - window_seconds:
        requests.popleft()

    # Check if rate limited
    if len(requests) >= max_requests:
        logger.warning(
            f"Rate limit exceeded for {identifier}: "
            f"{len(requests)}/{max_requests} requests"
        )
        return True

    # Add current request
    requests.append(current_time)
    return False


def validate_email_format(email: str) -> bool:
    """Enhanced email validation."""
    if not email or len(email) > 254:  # RFC 5321 limit
        return False

    # Basic RFC 5322 regex pattern
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        return False

    # Additional checks
    local, domain = email.split("@")
    if len(local) > 64:  # RFC 5321 limit for local part
        return False

    return True


def hash_password(password: str) -> str:
    """Hash the entire validated password; never truncate or normalize it."""
    return bcrypt.hashpw(password_bytes(password), bcrypt.gensalt(rounds=12)).decode(
        "ascii"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check standard legacy/new bcrypt hashes within the exact byte budget."""
    if not plain_password or not hashed_password:
        bcrypt.checkpw(b"dummy", _DUMMY_PASSWORD_HASH)
        return False
    try:
        encoded = password_bytes(plain_password)
        return bcrypt.checkpw(encoded, hashed_password.encode("ascii"))
    except (ValueError, TypeError, UnicodeError):
        # Do not expose submitted passwords or stored hashes through exceptions.
        logger.warning("Password verification rejected invalid input or hash")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with enhanced security."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

    # Add standard JWT claims
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": "orbitagents-auth",  # Issuer
            "aud": "orbitagents-platform",  # Audience
        }
    )

    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT encoding error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate access token",
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current user from JWT token with enhanced validation."""

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorization header required",
        )

    if not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )

    try:
        # Decode and validate JWT
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience="orbitagents-platform",
            issuer="orbitagents-auth",
        )

        email = payload.get("sub")
        if not isinstance(email, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
            )

        # Validate email format
        if not validate_email_format(email):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token email format",
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token validation failed"
        )

    # Get user from database
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )


@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: ValidationError | RequestValidationError
) -> JSONResponse:
    """Return useful error locations without raw inputs or exception contexts."""
    errors = [
        {key: error[key] for key in ("type", "loc", "msg") if key in error}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Input validation failed", "errors": errors},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle value errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database service temporarily unavailable"},
    )


@app.middleware("http")
async def add_process_time_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add request metrics and timing with enhanced security logging."""
    start_time = time.time()

    # Log security-relevant information
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_DURATION.observe(process_time)

        # Log suspicious activity
        if response.status_code >= 400:
            logger.warning(
                f"Failed request: {request.method} {request.url.path} "
                f"Status: {response.status_code} IP: {client_ip} "
                f"User-Agent: {user_agent}"
            )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Request error: {request.method} {request.url.path} "
            f"Error: {e} IP: {client_ip}"
        )

        REQUEST_COUNT.labels(
            method=request.method, endpoint=request.url.path, status=500
        ).inc()
        REQUEST_DURATION.observe(process_time)

        raise


@app.get("/healthz")
async def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """Health check endpoint for Kubernetes probes with enhanced validation."""
    try:
        # Test database connection with timeout
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy: Database connection failed",
        )


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    try:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        logger.error(f"Metrics generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics service error",
        )


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, request: Request, db: Session = Depends(get_db)
) -> UserResponse:
    """Register a new user with enhanced security and validation."""

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"register_{client_ip}", max_requests=5, window_seconds=300):
        REGISTRATION_ATTEMPTS.labels(status="rate_limited").inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )

    # Additional email validation
    if not validate_email_format(user_data.email):
        REGISTRATION_ATTEMPTS.labels(status="invalid_email").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format"
        )

    # Normalize email
    normalized_email = user_data.email.lower().strip()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            REGISTRATION_ATTEMPTS.labels(status="duplicate_email").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        hashed_password = hash_password(user_data.password)
        db_user = User(email=normalized_email, hashed_password=hashed_password)

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        REGISTRATION_ATTEMPTS.labels(status="success").inc()
        logger.info(f"User registered successfully: {normalized_email}")

        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            created_at=db_user.created_at,
            is_active=db_user.is_active,
        )

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Registration integrity error: {e}")
        REGISTRATION_ATTEMPTS.labels(status="duplicate_email").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {e}")
        REGISTRATION_ATTEMPTS.labels(status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service temporarily unavailable",
        )


@app.post("/login", response_model=Token)
async def login(
    user_credentials: UserLogin, request: Request, db: Session = Depends(get_db)
) -> Token:
    """Authenticate user and return JWT token with enhanced security."""

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if is_rate_limited(f"login_{client_ip}", max_requests=10, window_seconds=300):
        LOGIN_ATTEMPTS.labels(status="rate_limited").inc()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    # Normalize email
    normalized_email = user_credentials.email.lower().strip()

    try:
        # Find user
        user = db.query(User).filter(User.email == normalized_email).first()

        # Verify password (always takes same time whether user exists or not)
        password_valid = False
        if user:
            password_valid = verify_password(
                user_credentials.password, user.hashed_password
            )
        else:
            # Perform dummy password verification to prevent timing attacks
            bcrypt.checkpw(b"dummy", _DUMMY_PASSWORD_HASH)

        if not user or not password_valid:
            LOGIN_ATTEMPTS.labels(status="failed").inc()
            logger.warning(
                f"Failed login attempt for: {normalized_email} from IP: {client_ip}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not user.is_active:
            LOGIN_ATTEMPTS.labels(status="inactive").inc()
            logger.warning(f"Login attempt for inactive user: {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive"
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        LOGIN_ATTEMPTS.labels(status="success").inc()
        logger.info(f"Successful login: {normalized_email}")

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRATION_MINUTES * 60,  # Convert to seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        LOGIN_ATTEMPTS.labels(status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable",
        )


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get current user information with enhanced validation."""
    try:
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            created_at=current_user.created_at,
            is_active=current_user.is_active,
        )
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User service temporarily unavailable",
        )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, access_log=True)
