# Bite Me Buddy - Food Ordering System

Professional mobile-friendly food ordering website with secret admin access.

## Features
- Customer registration & login
- Service-based menu browsing
- Cart management & order placement
- Team member order management with OTP verification
- Admin panel for full system management
- Real-time session tracking
- Twilio OTP SMS integration
- Secret admin access via clock interaction

## Tech Stack
- Backend: Python 3.11 + FastAPI (async)
- Database: PostgreSQL + SQLAlchemy 2.0
- Frontend: Jinja2 + Bootstrap 5 + HTMX
- Security: bcrypt, JWT tokens, HTTP-only cookies

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repository-url>
cd bite-me-buddy
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database and Twilio credentials
# Create database
createdb bitemebuddy

# Run migrations
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
# Run tests
pytest