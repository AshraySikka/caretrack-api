# CareTrack API
### Author: Ashray Sikka

A production-style REST API for managing patient care coordination, built with FastAPI and PostgreSQL.

Inspired by real workflows from healthcare coordination — managing patients, assigning providers, creating care plans, and scheduling appointments.

## Live API

> **Live API:** https://caretrack-api.onrender.com
> 
> **Interactive Docs:** https://caretrack-api.onrender.com/docs

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Authentication | JWT (python-jose + bcrypt) |
| Validation | Pydantic v2 |
| Runtime | Python 3.13 |
| Local DB | Docker |

## Features

- JWT authentication with role-based access control (coordinator / admin)
- Full CRUD for patients, providers, care plans, and appointments
- Care plan status transitions with business rule enforcement
- Appointment scheduling with date range filtering
- Nested response objects (patient → coordinator, care plan → provider)
- Pagination and filtering on all list endpoints
- Database migrations with Alembic version control

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register` | Register new account | No |
| POST | `/api/v1/auth/login` | Login, returns JWT token | No |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |
| PUT | `/api/v1/auth/me` | Update own profile | Yes |

### Patients
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/patients/` | List patients (paginated, filterable) | Yes |
| POST | `/api/v1/patients/` | Create new patient | Yes |
| GET | `/api/v1/patients/{id}` | Get patient by ID | Yes |
| PUT | `/api/v1/patients/{id}` | Update patient | Yes |
| DELETE | `/api/v1/patients/{id}` | Discharge patient | Admin |
| GET | `/api/v1/patients/{id}/care-plans` | Patient's care plans | Yes |
| GET | `/api/v1/patients/{id}/appointments` | Patient's appointments | Yes |

### Providers
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/providers/` | List providers (filter by type, availability) | Yes |
| POST | `/api/v1/providers/` | Add new provider | Admin |
| GET | `/api/v1/providers/{id}` | Get provider by ID | Yes |
| PUT | `/api/v1/providers/{id}` | Update provider | Admin |
| GET | `/api/v1/providers/{id}/schedule` | Provider schedule | Yes |

### Care Plans
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/care-plans/` | List care plans (filter by status, patient) | Yes |
| POST | `/api/v1/care-plans/` | Create care plan | Yes |
| GET | `/api/v1/care-plans/{id}` | Get care plan by ID | Yes |
| PUT | `/api/v1/care-plans/{id}` | Update care plan | Yes |
| PATCH | `/api/v1/care-plans/{id}/status` | Change plan status | Yes |
| DELETE | `/api/v1/care-plans/{id}` | Delete draft plan | Yes |

### Appointments
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/appointments/upcoming` | Next 7 days appointments | Yes |
| GET | `/api/v1/appointments/` | List appointments (filterable) | Yes |
| POST | `/api/v1/appointments/` | Schedule appointment | Yes |
| GET | `/api/v1/appointments/{id}` | Get appointment by ID | Yes |
| PUT | `/api/v1/appointments/{id}` | Update appointment | Yes |
| PATCH | `/api/v1/appointments/{id}/status` | Mark complete/cancel/no-show | Yes |

## Database Schema
```
users
  id, email, full_name, hashed_password, role, is_active, created_at, updated_at

patients
  id, first_name, last_name, date_of_birth, health_card_no, phone, email,
  address, status, assigned_coordinator_id (→ users), created_at, updated_at

providers
  id, first_name, last_name, provider_type, license_number, phone, email,
  max_patients, is_available, created_at, updated_at

care_plans
  id, patient_id (→ patients), provider_id (→ providers), created_by (→ users),
  title, description, goals, status, start_date, end_date, created_at, updated_at

appointments
  id, patient_id (→ patients), provider_id (→ providers), care_plan_id (→ care_plans),
  scheduled_at, duration_mins, visit_type, status, notes, created_at, updated_at
```

## Local Setup

### Prerequisites
- Python 3.12+
- Docker Desktop
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/AshraySikka/caretrack-api.git
cd caretrack-api
```

2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file
```bash
cp .env.example .env
```

Edit `.env` with your values:
```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/caretrack
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

5. Start PostgreSQL with Docker
```bash
docker compose up -d
```

6. Run database migrations
```bash
alembic upgrade head
```

7. Start the server
```bash
uvicorn app.main:app --reload --reload-dir app
```

8. Open API docs
```
http://127.0.0.1:8000/docs
```

## Project Structure
```
caretrack-api/
├── alembic/              # Database migrations
├── app/
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── routers/          # FastAPI route handlers
│   ├── services/         # Business logic layer
│   ├── utils/            # Security utilities
│   ├── config.py         # Settings management
│   ├── database.py       # Database connection
│   ├── dependencies.py   # Auth dependencies
│   └── main.py           # Application entry point
└── tests/                # Test suite
```

## Authentication

The API uses JWT Bearer token authentication.

1. Register: `POST /api/v1/auth/register`
2. Login: `POST /api/v1/auth/login` — returns access token
3. Use token in header: `Authorization: Bearer <token>`

Two roles are supported:
- `coordinator` — standard access (default)
- `admin` — full access including provider management and patient discharge