# Payer Platform

A backend health-insurer simulation covering eligibility, prior authorization and claims adjudication.

Inspired by healthcare payer workflows and FHIR interoperability standards — not a claim of HIPAA/CMS compliance. Synthetic data only, never real PHI.

## Table of Contents

- [Overview](#overview)
- [Highlights](#highlights)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [License](#license)

## Overview

This project implements the core workflows of a health insurer's backend: verifying member eligibility, processing prior authorization requests through a rules engine and adjudicating claims with a full audit trail — built as a synchronous, single-service system first with distributed-systems concerns (caching, background jobs, event streaming) layered in as the system grows.

## Highlights

- **~1,624x query speedup** on a realistic query at 2M+ real rows (443 ms → 0.27 ms) via a composite index, measured directly with `EXPLAIN ANALYZE` before and after.
- **~35–40x faster bulk inserts** (14–16s → 0.41s for 10,000 rows) by switching from row-by-row ORM inserts to batched multi-row SQL statements.
- **A real, reproduced lost-update race condition**, fixed with optimistic locking (a conditional `UPDATE ... WHERE status == SUBMITTED`) — deliberately chosen over `SELECT ... FOR UPDATE` as the more representative real-world pattern for simple state-transition guards.
- **A real concurrent-retry race condition** (duplicate claim submission), fixed via a database `UNIQUE` constraint + graceful recovery from the resulting `IntegrityError` — proven that application-level checks alone cannot prevent this class of bug.
- **A 404-vs-403 existence-leak fix**, self-identified and corrected: resource ownership failures return the identical response whether a resource doesn't exist or just isn't yours.
- **A self-identified authorization gap**, found and fixed: any authenticated provider could view any patient's data with no relationship check at all.
- **A migration-autogenerate bug caught before running it**: Alembic's autogenerate turned a column rename into "drop + add," which would have destroyed the one real row in that table — caught by reviewing the diff, not trusting it blindly.

## Features

- **Eligibility checks** — member coverage status under a given insurance plan.
- **Prior authorization** — providers request pre-approval for a procedure; a rules engine decides approve/deny/manual-review based on coverage status, referral and treatment-history facts.
- **Claims adjudication** — providers bill for services rendered; the platform calculates insurance payment vs. patient responsibility, atomically with a full audit trail.
- **JWT-based authentication and role-based authorization** — provider and reviewer roles with resource-ownership enforcement.
- **Idempotent claim submission** — safe retries with no duplicate records, enforced at the database level.

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic v2
- **Database:** PostgreSQL 16
- **Migrations:** Alembic
- **Auth:** PyJWT
- **Testing:** pytest
- **Containers:** Docker Compose

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose

### Installation

```bash
git clone https://github.com/vamsisandilya/payer-platform.git
cd payer-platform

docker compose up -d              # start PostgreSQL
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

alembic upgrade head              # apply database migrations
uvicorn app.main:app --reload     # start the API
```

## Usage

Interactive API documentation (auto-generated from the code) is available once the server is running:

```
http://localhost:8000/docs
```

Generate a test JWT for authenticated requests:

```bash
python generate_token.py --provider-id 1 --role provider
```

## Project Structure

```
app/
  models.py     # SQLAlchemy models — the database schema
  schemas.py    # Pydantic schemas — the API's request/response contracts
  rules.py      # Pure business logic (no DB, no HTTP): prior-auth decisions, claims adjudication math
  auth.py       # JWT verification, role-based access, resource-ownership checks
  main.py       # HTTP endpoints
  database.py   # Engine, session management
alembic/        # Schema migration history
tests/          # Unit tests
generator.py    # Synthetic test-data generation
```

**Request flow:**
```
Client → FastAPI route → Depends() (auth, DB session) → Pydantic validation
  → endpoint logic (calls pure rules-engine functions where relevant)
  → SQLAlchemy session → PostgreSQL (one transaction per request, atomic commit)
  → Pydantic response schema → JSON
```

## Data Model

`Member`, `Provider`, `InsurancePlan`, `Coverage`, `PriorAuthorization`, `AuthorizationDecision`, `Claim`, `ClaimLine`, `AuditEvent`, `IdempotencyRecord`.

## Testing

```bash
pytest -v
```

## Roadmap

Phases 0–2 complete (Steps 1–9 of 21): domain modeling, correctness under real-world conditions (migrations, auth, idempotency, concurrency) and performance/scale (volume + indexing). In progress: Phase 3 (asynchrony & events — Redis, Celery, Kafka).

## License

MIT
