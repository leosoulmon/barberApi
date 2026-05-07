# Baron Barber API

Professional barber scheduling REST API built with **FastAPI** and **Clean Architecture**. This project demonstrates enterprise-grade Python patterns including strict type hinting, asynchronous programming, and decoupled layers.

## Features

- **User Management**: Distinct roles for Barbers (Service Providers) and Clients
- **Service Catalog**: CRUD operations for services with duration and pricing
- **Availability Management**: Working hours, lunch breaks, and time-off for barbers
- **Appointment Booking**: Real-time slot reservation with collision detection
- **Audit Trail**: History of appointments and status changes
- **JWT Authentication**: Secure OAuth2 password flow with bcrypt hashing

## Tech Stack

- **Python 3.12+**
- **FastAPI** — HTTP layer with automatic OpenAPI documentation
- **SQLModel / SQLAlchemy (async)** — ORM and database models
- **Pydantic v2** — Request/response validation
- **Alembic** — Database migrations
- **PostgreSQL** (production) / **aiosqlite** (dev/test)
- **python-jose + passlib[bcrypt]** — JWT auth and password hashing
- **pytest + pytest-asyncio + httpx** — Testing

## Architecture

This project follows **Clean Architecture** with 3 layers:

```
app/
├── domain/          # Pure business logic, no framework dependencies
│   ├── entities.py   # Domain entities (User, Service, Appointment, etc.)
│   └── protocols.py  # Repository contracts (typing.Protocol)
├── application/     # Use-case / service layer
│   ├── services.py   # Orchestrates domain logic
│   └── exceptions.py # Domain-specific exceptions
└── infrastructure/  # Framework and persistence details
    ├── models.py     # SQLModel DB models
    ├── schemas.py    # Pydantic request/response DTOs
    ├── mappers.py    # Entity ↔ Model bidirectional mappers
    ├── repositories.py # Async repository implementations
    ├── database.py   # Async SQLAlchemy engine setup
    ├── dependencies.py # FastAPI Depends() providers
    └── routes/       # API endpoints
        ├── auth.py
        ├── users.py
        ├── services.py
        ├── availability.py
        ├── appointments.py
        └── audit.py
```

### Layer Rules

- **Domain**: No FastAPI, SQLAlchemy, or Pydantic imports. Pure `@dataclass` entities.
- **Application**: Depends only on protocol interfaces, never on infrastructure.
- **Infrastructure**: Routes map Pydantic → Domain → Service → Response. Thin adapters only.

## Installation

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- (Optional) PostgreSQL for production

### 1. Clone the Repository

```bash
git clone https://github.com/leosoulmon/barberApi.git
cd barberApi
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the project root:

```env
# Database (PostgreSQL for production, SQLite for dev)
DATABASE_URL=sqlite+aiosqlite:///./barber.db
# For PostgreSQL: DATABASE_URL=postgresql+asyncpg://user:password@localhost/barber

# JWT Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Run the Application

```bash
# Development with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API Base**: http://localhost:8000/
- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | OAuth2 login (form data) |
| POST | `/api/v1/auth/register` | Register new user |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PATCH | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Delete user |

### Services

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/services` | List all services |
| POST | `/api/v1/services` | Create service (barber only) |
| GET | `/api/v1/services/{id}` | Get service by ID |
| PATCH | `/api/v1/services/{id}` | Update service |
| DELETE | `/api/v1/services/{id}` | Delete service |

### Availability

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/availability` | List availability slots |
| GET | `/api/v1/availability/barber/{barber_id}` | Get barber availability |
| POST | `/api/v1/availability` | Create availability slot (barber only) |
| POST | `/api/v1/availability/timeoff` | Add time-off (barber only) |
| GET | `/api/v1/availability/slots/{barber_id}` | Get available booking slots |

### Appointments

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/appointments` | List appointments |
| POST | `/api/v1/appointments` | Book appointment (client only) |
| GET | `/api/v1/appointments/{id}` | Get appointment by ID |
| PATCH | `/api/v1/appointments/{id}` | Update appointment |
| POST | `/api/v1/appointments/{id}/complete` | Mark as completed |
| POST | `/api/v1/appointments/{id}/cancel` | Cancel appointment |
| DELETE | `/api/v1/appointments/{id}` | Delete appointment |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit` | List audit logs (admin only) |
| GET | `/api/v1/audit/appointment/{id}` | Get logs for appointment |

## Usage Examples

### 1. Register a Barber

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "barber@example.com",
    "password": "securepassword",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "role": "barber"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=barber@example.com&password=securepassword"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Create a Service (as Barber)

```bash
curl -X POST "http://localhost:8000/api/v1/services" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Haircut",
    "description": "Classic men's haircut",
    "duration_minutes": 30,
    "price": 25.00
  }'
```

### 4. Set Availability (as Barber)

```bash
curl -X POST "http://localhost:8000/api/v1/availability" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "day_of_week": 1,
    "start_time": "09:00:00",
    "end_time": "18:00:00"
  }'
```

### 5. Book an Appointment (as Client)

```bash
curl -X POST "http://localhost:8000/api/v1/appointments" \
  -H "Authorization: Bearer <client_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "barber_id": "<barber_uuid>",
    "service_id": "<service_uuid>",
    "start_time": "2024-06-15T10:00:00"
  }'
```

## Testing

### Run Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html
```

### Test Structure

- **Unit tests**: Domain logic in isolation (mocks for repositories)
- **Integration tests**: Full API flow with `httpx.AsyncClient` and SQLite

## Database Migrations (Alembic)

```bash
# Initialize migrations (first time only)
alembic init migrations

# Create migration
alembic revision --autogenerate -m "initial migration"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Development Guidelines

### Code Style

- Full **type annotations** required on all functions
- **Docstrings** for all public classes and functions
- Use `async`/`await` throughout; no synchronous DB calls
- Import order: stdlib → third-party → local; use absolute imports

### Naming Conventions

| Layer | Convention | Example |
|-------|------------|---------|
| Domain entities | PascalCase dataclass | `Appointment` |
| DB models | `<Entity>Model` | `AppointmentModel` |
| Pydantic schemas | `<Entity>Create/Update/Response` | `AppointmentCreate` |
| Mappers | `<Entity>Mapper` | `AppointmentMapper` |
| Repositories | `<Entity>Repository` | `AppointmentRepository` |
| Routes | plural snake_case | `appointments.py` |

## Project Roadmap

See [ROADMAP.md](./ROADMAP.md) for planned features and improvements.

## Security Notes

- Never commit `.env` files or secrets to version control
- Use strong `SECRET_KEY` in production (32+ bytes random)
- Enable HTTPS in production
- Review and update dependencies regularly

## License

[MIT License](LICENSE)
