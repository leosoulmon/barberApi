"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from .infrastructure.database import init_db
from .infrastructure.routes import auth, users, services, availability, appointments, audit


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Barber Scheduling API",
    description="Professional barber scheduling API with clean architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(availability.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")


@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint."""
    return {
        "message": "Barber Scheduling API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

