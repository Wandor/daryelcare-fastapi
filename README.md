# ReadyKids Childminder Agency Portal (FastAPI)

A full-stack registration and admin portal for a childminder agency, built with FastAPI and PostgreSQL.

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, asyncpg
- **Database:** PostgreSQL with JSONB columns for nested form data
- **Frontend:** Vanilla HTML/CSS/JS (no build step)

## Prerequisites

- **Python** 3.11+
- **PostgreSQL** 14+

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the PostgreSQL database
createdb readykids

# 4. Configure environment
cp .env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```
DATABASE_URL=postgres://postgres:yourpassword@localhost:5432/readykids
PORT=3000
```

## Seeding Demo Data

```bash
python seed.py
```

Seeds 11 sample applications across all pipeline stages. Idempotent and safe to run multiple times.

## Running

```bash
# Production
uvicorn app.main:app --host 0.0.0.0 --port 3000

# Development (auto-reload)
python app/main.py
```

The server starts at **http://localhost:3000**.

## Pages

| URL | Description |
|-----|-------------|
| http://localhost:3000/register | 9-section childminder registration form |
| http://localhost:3000/admin | Admin dashboard with pipeline view and compliance tracking |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/applications` | List all applications |
| GET | `/api/applications/{id}` | Get single application |
| POST | `/api/applications` | Submit new registration |
| PATCH | `/api/applications/{id}` | Update application fields |
| DELETE | `/api/applications/{id}` | Remove application |
| POST | `/api/applications/{id}/timeline` | Add audit log entry |

## Resetting the Database

```bash
dropdb readykids
createdb readykids
python seed.py
```
