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

**Get Token:**
```bash
POST /api/api/auth/token/
Content-Type: application/json

{
    "username": "admin@example.com",
    "password": "your_password"
}
```

**Use Token in Headers:**
```bash
Authorization: Token your_token_here
```

### API Endpoints

#### User Management
- `GET /api/api/users/` - List all users (with filtering, search, pagination)
- `POST /api/api/users/` - Create new user
- `GET /api/api/users/{id}/` - Get specific user details
- `PUT /api/api/users/{id}/` - Update user (full update)
- `PATCH /api/api/users/{id}/` - Partial update user
- `DELETE /api/api/users/{id}/` - Deactivate user (soft delete)
- `POST /api/api/users/{id}/activate/` - Reactivate deactivated user
- `GET /api/api/users/drivers/` - Get all active drivers
- `GET /api/api/users/riders/` - Get all active riders
- `GET /api/api/users/{id}/rides/` - Get all rides for specific user
- `GET /api/api/users/stats/` - Get user statistics dashboard

#### Ride Management
- `GET /api/api/rides/` - List rides (supports GPS sorting, filtering, pagination)
- `POST /api/api/rides/` - Create new ride
- `GET /api/api/rides/{id}/` - Get specific ride with events
- `PUT /api/api/rides/{id}/` - Update ride (full update)
- `PATCH /api/api/rides/{id}/` - Partial update ride
- `DELETE /api/api/rides/{id}/` - Delete ride
- `GET /api/api/rides/nearby/` - Find rides near GPS coordinates
- `GET /api/api/rides/{id}/events/` - Get all events for specific ride
- `GET /api/api/rides/active/` - Get all active (non-completed) rides
- `GET /api/api/rides/stats/` - Get ride statistics dashboard

#### Ride Event Management
- `GET /api/api/ride-events/` - List ride events (with filtering, search, pagination)
- `POST /api/api/ride-events/` - Create new ride event
- `GET /api/api/ride-events/{id}/` - Get specific ride event
- `PUT /api/api/ride-events/{id}/` - Update ride event (full update)
- `PATCH /api/api/ride-events/{id}/` - Partial update ride event
- `DELETE /api/api/ride-events/{id}/` - Delete ride event
- `GET /api/api/ride-events/todays_events/` - Get today's events (performance optimized)
- `GET /api/api/ride-events/by_ride/?ride_id={id}` - Get events for specific ride
- `GET /api/api/ride-events/event_types/` - Get all unique event types
- `GET /api/api/ride-events/stats/` - Get ride event statistics

### Special Features

#### GPS-Based Sorting
Add GPS parameters to ride list to sort by distance:
```bash
GET /api/api/rides/?gps_latitude=37.7749&gps_longitude=-122.4194
```

#### Nearby Rides
Find rides within a radius (default 10km):
```bash
GET /api/api/rides/nearby/?gps_latitude=37.7749&gps_longitude=-122.4194&radius=5
```

#### Today's Events (Performance Optimized)
Get events from last 24 hours with pagination:
```bash
GET /api/api/ride-events/todays_events/
```

#### Filtering Examples
```bash
# Filter users by role
GET /api/api/users/?role=driver&is_active=true

# Filter rides by status and date
GET /api/api/rides/?status=active&start_date=2025-01-01

# Search users by name or email
GET /api/api/users/?search=john

# Filter events by type and ride
GET /api/api/ride-events/?event_type=pickup&ride_id=123
```

### Interactive API Browser

Visit `/api/api/` in your browser after starting the server to access Django REST Framework's interactive API browser for testing endpoints.

## Development

This project follows Django best practices and includes:

- Environment-based configuration
- PostgreSQL for both development and production
- Comprehensive error handling
- Performance optimizations for large datasets
