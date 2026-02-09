# FastAPI Tutoring/Therapy Scheduler Backend

This is the backend for a multi-tenant scheduling application where providers (tutors/therapists) can manage their availability and clients can book appointments.

## API Documentation

### Base URL
`http://localhost:8000/api/v1`

---

### 1. Authentication (`/auth`)
Managed via `fastapi-users`.

*   **POST `/auth/register`**: Register a new user.
    *   **Body**: `{"email": "user@example.com", "password": "...", "full_name": "...", "role": "tutor|client"}`
*   **POST `/auth/jwt/login`**: Login to receive a JWT.
    *   **Body**: `username=email&password=password` (Form data)
*   **POST `/auth/jwt/logout`**: Logout.

---

### 2. Users (`/users`)
*   **GET `/users/me`**: Get current user profile.
*   **PATCH `/users/me`**: Update current user profile.

---

### 3. Tutors (`/tutors`)
*   **POST `/tutors/me`**: Create a tutor profile (Requires `tutor` role).
    *   **Body**: `{"public_handle": "unique-slug", "specialty": "Math", "bio": "...", "session_duration_minutes": 60}`
*   **GET `/tutors/me`**: Get current tutor profile.
*   **PUT `/tutors/me`**: Update current tutor profile.
*   **GET `/tutors/availability`**: Get availability slots for a specific date.
    *   **Params**: `tutor_id` (UUID), `date` (YYYY-MM-DD)
*   **GET `/tutors/{public_handle}`**: Publicly view a tutor's profile.
*   **POST `/tutors/me/availability`**: Add a weekly availability pattern.
    *   **Body**: `{"day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00"}`
*   **GET `/tutors/{public_handle}/availability`**: Get a tutor's active availability patterns.
*   **PUT `/tutors/me/availability/{id}`**: Update availability pattern.
*   **DELETE `/tutors/me/availability/{id}`**: Remove availability pattern.

---

### 4. Appointments (`/appointments`)
*   **POST `/appointments/`**: Book an appointment.
    *   **Body (Registered Client)**: `{"tutor_id": "UUID", "start_datetime": "ISO-8601", "end_datetime": "ISO-8601", "notes": "..."}`
    *   **Body (Guest)**: Includes `"guest_details": {"name": "...", "email": "..."}`
*   **GET `/appointments/me`**: List appointments for the current user (as client or tutor).
*   **PATCH `/appointments/{id}/status`**: Update appointment status (Tutor only).
    *   **Body**: `{"status": "confirmed|declined|cancelled"}`

---

## Getting Started

### Prerequisites
*   [uv](https://github.com/astral-sh/uv)
*   Docker & Docker Compose

### Setup
1.  **Environment**:
    ```bash
    cp .env.example .env
    # Edit .env with your database credentials and secret key
    ```

2.  **Infrastructure**:
    ```bash
    docker-compose up -d db
    ```

3.  **Run Server**:
    ```bash
    uv run uvicorn main:app --reload
    ```

### Interactive Docs
*   Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
*   ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Development
*   **Timezones**: All logic assumes `America/Guayaquil` (Quito).
*   **Models**: SQLAlchemy Async models.
*   **Linting/Formatting**: Standard Python conventions.
