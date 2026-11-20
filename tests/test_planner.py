from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from app import create_app, calculate_gpa, get_academic_standing, parse_date


def test_parse_date_valid_and_invalid():
    d = parse_date("2026-11-19")
    assert d is not None
    assert d.year == 2026 and d.month == 11 and d.day == 19
    assert parse_date("invalid-date") is None
    assert parse_date("") is None


def test_calculate_gpa_and_academic_standing():
    entries = [
        SimpleNamespace(grade="A", credits=4.0),
        SimpleNamespace(grade="B", credits=3.0),
    ]
    assert calculate_gpa(entries) == 3.57
    assert calculate_gpa([]) == 0.0
    assert get_academic_standing(3.85, 4) == "Dean's List"
    assert get_academic_standing(3.57, 2) == "Good Standing"
    assert get_academic_standing(1.65, 2) == "Academic Warning"
    assert get_academic_standing(0.0, 0) == "No Grades Recorded"


def test_health_and_auth_flow():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
    })
    client = app.test_client()

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.get_json()["status"] == "healthy"

    # Register & login
    reg = client.post("/register", data={
        "username": "student1",
        "email": "student1@example.com",
        "password": "password123",
        "confirm_password": "password123",
    }, follow_redirects=True)
    assert reg.status_code == 200

    login = client.post("/login", data={
        "email": "student1@example.com",
        "password": "password123",
    }, follow_redirects=True)
    assert login.status_code == 200

    today = datetime.now(timezone.utc).date()
    due_soon = (today + timedelta(days=2)).isoformat()
    overdue_day = (today - timedelta(days=2)).isoformat()

    client.post("/tasks/new", data={
        "title": "Linear Algebra Problem Set",
        "description": "Eigenvalues & SVD",
        "due_date": due_soon,
        "priority": "High",
        "status": "In progress",
    }, follow_redirects=True)

    client.post("/tasks/new", data={
        "title": "Past Due Reading",
        "description": "Chapter 3",
        "due_date": overdue_day,
        "priority": "Medium",
        "status": "Not started",
    }, follow_redirects=True)

    # Reject empty title on edit
    client.post("/tasks/1/edit", data={"title": "   "}, follow_redirects=True)

    upcoming = client.get("/api/tasks/upcoming?days=7")
    assert upcoming.status_code == 200
    upcoming_json = upcoming.get_json()
    assert upcoming_json["count"] == 1
    assert upcoming_json["tasks"][0]["title"] == "Linear Algebra Problem Set"

    stats = client.get("/api/stats")
    assert stats.status_code == 200
    stats_json = stats.get_json()
    assert stats_json["total_tasks"] == 2
    assert stats_json["overdue_tasks"] == 1
    assert stats_json["academic_standing"] == "No Grades Recorded"
