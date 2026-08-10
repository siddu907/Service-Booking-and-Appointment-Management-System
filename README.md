# Service Booking & Appointment Management System

This project implements a FastAPI backend for a service booking platform with authentication, services, availability, bookings, payments, reviews, notifications, dashboards, and file uploads.

## Features
- JWT authentication with role-based access control
- Service management for providers
- Availability slot management with overlap prevention
- Appointment booking, confirmation, cancellation, rescheduling, and completion
- Payment simulation and refunds
- Reviews and provider ratings
- Notification support and background reminder tasks
- Dashboard summaries for admin and providers
- File upload handling for profile and service images

## Setup

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```
On Windows PowerShell:
```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment variables
Copy `.env.example` to `.env` and update the values if needed.

### 4. Set up the database
This project uses SQLAlchemy with Alembic migrations.

If you are using the default PostgreSQL configuration, make sure PostgreSQL is running and the database exists.

To initialize the schema locally:
```bash
alembic upgrade head
```

### 5. Start Redis (required for cache functionality)
If Redis is installed locally, start it on port 6379:
```bash
redis-server
```

### 6. Run the application
```bash
uvicorn app.main:app --reload
```

The API will be available at:
- Swagger UI: http://127.0.0.1:8000/docs

## API Documentation
- Swagger UI: http://127.0.0.1:8000/docs
- Separate endpoint reference: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## Testing
Run `pytest`.

## Notes
- The default configuration uses PostgreSQL for local development and deployment.
- Ensure the PostgreSQL server is running and the database exists before starting the app.
