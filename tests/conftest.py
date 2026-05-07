"""Shared test fixtures for unit and integration tests."""
import asyncio
from datetime import datetime, time, timedelta
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.infrastructure.database import get_session
from app.infrastructure.dependencies import (
    get_password_hash, create_access_token,
)
from app.main import app


# ────────────────────────────────────────────────────────────────────────────
# Async event loop
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ────────────────────────────────────────────────────────────────────────────
# Database fixtures (in-memory SQLite)
# ────────────────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide test DB session."""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_session] = override_get_session


# ────────────────────────────────────────────────────────────────────────────
# HTTP client fixture
# ────────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for integration tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ────────────────────────────────────────────────────────────────────────────
# Auth helpers
# ────────────────────────────────────────────────────────────────────────────

def make_auth_header(user_id: str, email: str = "test@test.com", role: str = "client") -> dict:
    """Generate a Bearer token header for testing."""
    token = create_access_token(
        data={"sub": user_id, "email": email, "role": role},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def barber_id() -> str:
    """Return a consistent barber UUID string."""
    return str(uuid4())


@pytest.fixture
def client_id() -> str:
    """Return a consistent client UUID string."""
    return str(uuid4())


@pytest.fixture
def barber_headers(barber_id: str) -> dict:
    """Auth headers for a barber user."""
    return make_auth_header(barber_id, "barber@test.com", "barber")


@pytest.fixture
def client_headers(client_id: str) -> dict:
    """Auth headers for a client user."""
    return make_auth_header(client_id, "client@test.com", "client")
