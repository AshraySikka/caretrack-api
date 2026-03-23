from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, patients, providers, care_plans

app = FastAPI(
    title="CareTrack API",
    description="Patient care coordination REST API built with FastAPI and PostgreSQL",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(providers.router)
app.include_router(care_plans.router)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "CareTrack API is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}