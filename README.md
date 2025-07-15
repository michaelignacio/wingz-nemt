# Wingz NEMT - Django REST API

A RESTful API for managing ride information using Django REST Framework.

## Prerequisites

- Python 3.13+
- PostgreSQL 12+
- pipenv

## Database Setup

### PostgreSQL Installation

**macOS (with Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Database Creation

1. Connect to PostgreSQL as superuser:
```bash
psql postgres
```

2. Create database and user:
```sql
CREATE DATABASE wingz_nemt_dev;
CREATE USER postgres WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE wingz_nemt_dev TO postgres;
\q
```

## Project Setup

1. Clone the repository and navigate to project directory
2. Install dependencies:
```bash
pipenv install
```

3. Activate virtual environment:
```bash
pipenv shell
```

4. Copy environment variables:
```bash
cp .env.example .env
```

5. Update `.env` with your database credentials if different from defaults

6. Run migrations:
```bash
python manage.py migrate
```

7. Create superuser:
```bash
python manage.py createsuperuser
```

8. Start development server:
```bash
python manage.py runserver
```

## Environment Variables

- `DEBUG`: Set to `True` for development, `False` for production
- `SECRET_KEY`: Django secret key (generate a new one for production)
- `DATABASE_URL`: PostgreSQL connection string

## API Documentation

The API provides admin-only access to ride management with the following features:

- Ride List API with pagination, filtering, and sorting
- Performance optimized queries
- GPS-based distance sorting
- Real-time ride events tracking

### Authentication

All endpoints require admin authentication. Only users with 'admin' role can access the API.

## Development

This project follows Django best practices and includes:

- Environment-based configuration
- PostgreSQL for both development and production
- Comprehensive error handling
- Performance optimizations for large datasets
