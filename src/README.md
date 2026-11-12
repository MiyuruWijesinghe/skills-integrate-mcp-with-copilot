# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher sign-in to register and unregister students

## Teacher sign-in configuration

Set these environment variables before starting the application:

- `TEACHER_USERNAME`: the teacher account username
- `TEACHER_PASSWORD`: the teacher account password
- `SESSION_SECRET`: a randomly generated secret with at least 32 characters
- `COOKIE_SECURE`: optional; set to `true` when HTTPS is terminated by a reverse proxy

Keep these values out of source control. For local HTTP development, the session
cookie is not marked `Secure`; HTTPS requests use a `Secure` cookie by default.

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| GET    | `/auth/status`                                                    | Check whether the current browser is signed in as a teacher         |
| POST   | `/auth/login`                                                     | Sign in with the configured teacher username and password           |
| POST   | `/auth/logout`                                                    | Sign out the current browser                                        |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Teacher-only student signup                                         |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Teacher-only student removal                                      |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
