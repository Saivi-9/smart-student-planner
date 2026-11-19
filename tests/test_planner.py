from types import SimpleNamespace
from app import create_app, calculate_gpa, parse_date


def test_parse_date_valid_and_invalid():
    d = parse_date("2026-11-19")
    assert d is not None
    assert d.year == 2026 and d.month == 11 and d.day == 19
    assert parse_date("invalid-date") is None
    assert parse_date("") is None


def test_calculate_gpa_credit_weighted():
    entries = [
        SimpleNamespace(grade="A", credits=4.0),
        SimpleNamespace(grade="B", credits=3.0),
    ]
    assert calculate_gpa(entries) == 3.57
    assert calculate_gpa([]) == 0.0


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

    stats = client.get("/api/stats")
    assert stats.status_code == 200
    assert stats.get_json()["total_tasks"] == 0
