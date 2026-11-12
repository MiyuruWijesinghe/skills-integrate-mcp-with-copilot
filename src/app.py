"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}

TEACHER_SESSION_COOKIE = "teacher_session"
TEACHER_SESSION_DURATION = 8 * 60 * 60


class TeacherCredentials(BaseModel):
    username: str
    password: str


def _teacher_auth_config() -> tuple[str, str, str]:
    username = os.getenv("TEACHER_USERNAME")
    password = os.getenv("TEACHER_PASSWORD")
    session_secret = os.getenv("SESSION_SECRET")

    if not username or not password or not session_secret:
        raise HTTPException(
            status_code=503,
            detail=(
                "Teacher sign-in is not configured. Set TEACHER_USERNAME, "
                "TEACHER_PASSWORD, and SESSION_SECRET."
            ),
        )
    if len(session_secret) < 32:
        raise HTTPException(
            status_code=503,
            detail="SESSION_SECRET must be at least 32 characters long.",
        )

    return username, password, session_secret


def _create_teacher_session(session_secret: str) -> str:
    expires_at = str(int(time.time()) + TEACHER_SESSION_DURATION)
    signature = hmac.new(
        session_secret.encode("utf-8"),
        expires_at.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{expires_at}.{signature}"


def _has_teacher_session(request: Request, session_secret: str) -> bool:
    session = request.cookies.get(TEACHER_SESSION_COOKIE)
    if not session:
        return False

    try:
        expires_at, signature = session.split(".", 1)
        if int(expires_at) <= int(time.time()):
            return False
        expires_at_bytes = expires_at.encode("ascii")
    except (UnicodeEncodeError, ValueError):
        return False

    expected_signature = hmac.new(
        session_secret.encode("utf-8"),
        expires_at_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


def _require_teacher(request: Request) -> None:
    _, _, session_secret = _teacher_auth_config()
    if not _has_teacher_session(request, session_secret):
        raise HTTPException(status_code=401, detail="Teacher sign-in is required.")


def _secure_cookie(request: Request) -> bool:
    configured_value = os.getenv("COOKIE_SECURE")
    if configured_value is None:
        return request.url.scheme == "https"
    if configured_value.lower() not in {"true", "false"}:
        raise HTTPException(
            status_code=503,
            detail="COOKIE_SECURE must be set to 'true' or 'false'.",
        )
    return configured_value.lower() == "true"


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/auth/status")
def get_auth_status(request: Request):
    _, _, session_secret = _teacher_auth_config()
    return {"authenticated": _has_teacher_session(request, session_secret)}


@app.post("/auth/login")
def login(
    credentials: TeacherCredentials,
    request: Request,
    response: Response,
):
    configured_username, configured_password, session_secret = (
        _teacher_auth_config()
    )
    username_matches = hmac.compare_digest(
        credentials.username.encode("utf-8"),
        configured_username.encode("utf-8"),
    )
    password_matches = hmac.compare_digest(
        credentials.password.encode("utf-8"),
        configured_password.encode("utf-8"),
    )
    if not username_matches or not password_matches:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    response.set_cookie(
        key=TEACHER_SESSION_COOKIE,
        value=_create_teacher_session(session_secret),
        max_age=TEACHER_SESSION_DURATION,
        httponly=True,
        secure=_secure_cookie(request),
        samesite="strict",
    )
    return {"message": "Signed in successfully."}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    response.delete_cookie(
        key=TEACHER_SESSION_COOKIE,
        httponly=True,
        secure=_secure_cookie(request),
        samesite="strict",
    )
    return {"message": "Signed out successfully."}


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, request: Request):
    """Sign up a student for an activity"""
    _require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, request: Request):
    """Unregister a student from an activity"""
    _require_teacher(request)

    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
