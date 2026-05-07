# Changelog

## [1.0.0] - 2025-05-07

### Added

#### Project Structure & Entry Point
- `app/main.py` — FastAPI application with lifespan, CORS middleware, root and health endpoints
- `main.py` — Uvicorn entry point
- `requirements.txt` — all project dependencies
- `.windsurfrules` — project conventions and architecture reference
- `ROADMAP.md` — development roadmap and future improvements

#### Domain Layer (`app/domain/`)
- `entities.py` — `User`, `Service`, `AvailabilitySlot`, `TimeOff`, `Appointment`, `AuditLog` dataclass entities with enums (`UserRole`, `AppointmentStatus`, `WeekDay`)
- `entities.py` — business rules: `Appointment.is_overlapping()`, `Appointment.can_complete()`, `Appointment.can_cancel()`, `Appointment.get_duration()`
- `protocols.py` — repository contracts via `typing.Protocol` for `UserRepository`, `ServiceRepository`, `AvailabilityRepository`, `TimeOffRepository`, `AppointmentRepository`, `AuditRepository`

#### Application Layer (`app/application/`)
- `services.py` — `UserService` (CRUD, duplicate email check, list barbers)
- `services.py` — `ServiceCatalogService` (CRUD for barber services)
- `services.py` — `AvailabilityService` (slot CRUD, `is_barber_available()` with time-off conflict checking)
- `services.py` — `AppointmentBookingService` (book with collision detection, complete, cancel, reschedule, audit logging)
- `services.py` — `AuditService` (appointment history retrieval)
- `exceptions.py` — domain exceptions (`UserNotFoundError`, `DuplicateEmailError`, `AppointmentConflictError`, `BarberNotAvailableError`, etc.)

#### Infrastructure Layer (`app/infrastructure/`)
- `database.py` — async SQLAlchemy engine and session factory with env-based `DATABASE_URL`
- `models.py` — SQLModel database models for all 6 tables with relationships
- `schemas.py` — Pydantic v2 request/response DTOs with field validators (past-time rejection, end > start)
- `mappers.py` — bidirectional mappers (`UserMapper`, `ServiceMapper`, `AvailabilitySlotMapper`, `TimeOffMapper`, `AppointmentMapper`, `AuditLogMapper`)
- `repositories.py` — async SQL implementations of all 6 repository protocols
- `dependencies.py` — FastAPI `Depends()` providers for repos, services, JWT auth, password hashing, role guards (`require_barber`, `require_client`)

#### API Endpoints (`app/infrastructure/routes/`)
- `auth.py` — `POST /register`, `POST /login` (OAuth2 password flow), `GET /me`
- `users.py` — `GET /users`, `GET /users/barbers`, `GET /users/{id}`, `PUT /users/{id}`, `DELETE /users/{id}`
- `services.py` — `GET /services`, `GET /services/{id}`, `POST /services`, `PUT /services/{id}`, `DELETE /services/{id}`
- `availability.py` — `GET /availability/barbers/{id}`, `POST /availability/slots`, `PUT /availability/slots/{id}`, `DELETE /availability/slots/{id}`, `GET /availability/barbers/{id}/check`, `GET /availability/barbers/{id}/time-off`, `POST /availability/time-off`
- `appointments.py` — `GET /appointments`, `GET /appointments/{id}`, `POST /appointments`, `POST /appointments/{id}/complete`, `POST /appointments/{id}/cancel`, `POST /appointments/{id}/reschedule`
- `audit.py` — `GET /audit/appointments/{id}/history`, `GET /audit/appointments/{id}/history/{audit_id}`

#### Alembic Migrations
- `alembic.ini` — project-level Alembic configuration
- `alembic/env.py` — async-aware migration environment with `DATABASE_URL` env override
- `alembic/script.py.mako` — migration file template
- `alembic/versions/001_initial_schema.py` — initial migration covering all 6 tables (`users`, `services`, `availability_slots`, `time_offs`, `appointments`, `audit_logs`)

#### Production PostgreSQL Support
- `app/infrastructure/database.py` — reads `DATABASE_URL` environment variable; defaults to `sqlite+aiosqlite` for local development
- `requirements.txt` — replaced `psycopg2-binary` with `asyncpg` (async PostgreSQL driver)

#### Test Suite (61 tests)
- `pytest.ini` — pytest configuration with `asyncio_mode = auto`
- `tests/conftest.py` — shared fixtures: in-memory SQLite, async HTTP client, auth helpers
- `tests/unit/test_entities.py` — domain entity logic (overlap detection, lifecycle guards, duration)
- `tests/unit/test_services.py` — application services with mocked repositories (UserService, AppointmentBookingService, AvailabilityService)
- `tests/integration/test_auth.py` — register, login, `/me`, input validation
- `tests/integration/test_services_crud.py` — full service CRUD + barber role enforcement
- `tests/integration/test_availability.py` — availability slots, time-off, check endpoint, validation
- `tests/integration/test_appointments.py` — booking, conflict detection, cancel, complete, reschedule

### Fixed
- `app/infrastructure/routes/auth.py` — register endpoint now catches `DuplicateEmailError` and returns HTTP 409
- `app/infrastructure/models.py` — removed `from __future__ import annotations` to fix SQLAlchemy 2.x relationship resolution
- `app/infrastructure/dependencies.py` — explicit bcrypt rounds configuration for passlib compatibility
