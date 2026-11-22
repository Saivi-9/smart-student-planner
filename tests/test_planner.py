from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from app import (
    create_app,
    calculate_gpa,
    calculate_target_gpa_credits,
    get_academic_standing,
    parse_date,
    summarize_task_priorities,
    summarize_task_workload,
)


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
    # 7 credits totaling 25.0 quality points -> need 3.0 credits of A (4.0) to reach 3.70
    assert calculate_target_gpa_credits(entries, 3.7, "A") == 3.0
    assert calculate_target_gpa_credits(entries, 3.5, "A") == 0.0
    assert calculate_target_gpa_credits(entries, 4.0, "A") is None


def test_summarize_task_workload():
    today = datetime(2026, 11, 22, tzinfo=timezone.utc).date()
    sample_tasks = [
        SimpleNamespace(priority="High", status="In progress", due_date=today - timedelta(days=1)),
        SimpleNamespace(priority="High", status="Completed", due_date=today),
        SimpleNamespace(priority="Medium", status="Not started", due_date=today),
    ]
    w = summarize_task_workload(sample_tasks, today=today)
    assert w["total_tasks"] == 3
    assert w["completed_tasks"] == 1
    assert w["pending_tasks"] == 2
    assert w["completion_rate_pct"] == 33.3
    assert w["overdue_tasks"] == 1
    assert w["due_today_tasks"] == 1
    assert w["high_priority_pending"] == 1
    assert w["priority_breakdown"]["High"] == 2


    mock_tasks = [
        SimpleNamespace(priority="High", status="In progress"),
        SimpleNamespace(priority="High", status="Completed"),
        SimpleNamespace(priority="Low", status="Not started"),
    ]
    prio = summarize_task_priorities(mock_tasks)
    assert prio["total_tasks"] == 3
    assert prio["completed_tasks"] == 1
    assert prio["completion_rate_pct"] == 33.3
    assert prio["by_priority"]["High"]["pending"] == 1
    assert prio["by_priority"]["High"]["completed"] == 1
    assert prio["by_priority"]["Low"]["pending"] == 1




def test_health_and_auth_flow():
    pytest.importorskip("flask")
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

    client.post("/grades/new", data={"course": "Algorithms", "credits": "4", "grade": "A"}, follow_redirects=True)
    client.post("/grades/new", data={"course": "Databases", "credits": "3", "grade": "B"}, follow_redirects=True)

    target_res = client.get("/api/gpa/target?target=3.7&assumed_grade=A")
    assert target_res.status_code == 200
    target_json = target_res.get_json()
    assert target_json["current_gpa"] == 3.57
    assert target_json["completed_credits"] == 7.0
    assert target_json["required_credits"] == 3.0
    assert target_json["achievable"] is True

    prio_res = client.get("/api/tasks/priority-breakdown")
    assert prio_res.status_code == 200
    prio_json = prio_res.get_json()
    assert prio_json["total_tasks"] == 2
    assert prio_json["by_priority"]["High"]["pending"] == 1
    assert prio_json["by_priority"]["Medium"]["pending"] == 1


