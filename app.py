import os
from datetime import datetime, timedelta, timezone

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import db, User, Task, Grade


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def calculate_gpa(entries):
    if not entries:
        return 0.0

    total_credits = sum(entry.credits for entry in entries)
    if total_credits <= 0:
        return 0.0

    total_points = sum(GRADE_POINTS.get(entry.grade, 0.0) * entry.credits for entry in entries)
    return round(total_points / total_credits, 2)


def get_academic_standing(gpa, courses_count):
    if courses_count <= 0:
        return "No Grades Recorded"
    if gpa >= 3.7:
        return "Dean's List"
    if gpa >= 2.0:
        return "Good Standing"
    return "Academic Warning"


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    @app.route("/api/health")
    def api_health():
        return jsonify({"status": "healthy", "service": "smart-student-planner"})

    @app.route("/")
    @login_required
    def dashboard():
        tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.due_date.asc()).all()
        grades = Grade.query.filter_by(user_id=current_user.id).all()
        gpa = calculate_gpa(grades)
        today = datetime.now(timezone.utc).date()
        upcoming = [task for task in tasks if task.due_date and task.due_date <= today + timedelta(days=3)]
        return render_template("dashboard.html", tasks=tasks, grades=grades, gpa=gpa, upcoming=upcoming, today=today)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not username or not email or not password:
                flash("Please complete all fields.", "warning")
            elif password != confirm_password:
                flash("Passwords do not match.", "danger")
            elif User.query.filter((User.username == username) | (User.email == email)).first():
                flash("A user with that name or email already exists.", "danger")
            else:
                hashed_password = generate_password_hash(password)
                user = User(username=username, email=email, password_hash=hashed_password)
                db.session.add(user)
                db.session.commit()
                flash("Your account has been created. Please log in.", "success")
                return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash(f"Welcome back, {user.username}!", "success")
                return redirect(url_for("dashboard"))

            flash("Email or password is incorrect.", "danger")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    @app.route("/tasks/new", methods=["GET", "POST"])
    @login_required
    def new_task():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            due_date = request.form.get("due_date")
            priority = request.form.get("priority", "Medium")
            status = request.form.get("status", "Not started")

            if not title:
                flash("Task title is required.", "warning")
            else:
                task = Task(
                    user_id=current_user.id,
                    title=title,
                    description=description,
                    due_date=parse_date(due_date),
                    priority=priority,
                    status=status,
                )
                db.session.add(task)
                db.session.commit()
                flash("Task created successfully.", "success")
                return redirect(url_for("dashboard"))

        return render_template("task_form.html", task=None)

    @app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

        if request.method == "POST":
            new_title = request.form.get("title", "").strip()
            if not new_title:
                flash("Task title is required.", "warning")
                return render_template("task_form.html", task=task)
            task.title = new_title
            task.description = request.form.get("description", "").strip()
            task.due_date = parse_date(request.form.get("due_date"))
            task.priority = request.form.get("priority", "Medium")
            task.status = request.form.get("status", "Not started")
            db.session.commit()
            flash("Task updated successfully.", "success")
            return redirect(url_for("dashboard"))

        return render_template("task_form.html", task=task)

    @app.route("/tasks/<int:task_id>/delete", methods=["POST"])
    @login_required
    def delete_task(task_id):
        task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted.", "info")
        return redirect(url_for("dashboard"))

    @app.route("/grades")
    @login_required
    def grades():
        grades = Grade.query.filter_by(user_id=current_user.id).order_by(Grade.course.asc()).all()
        gpa = calculate_gpa(grades)
        return render_template("grades.html", grades=grades, gpa=gpa)

    @app.route("/grades/new", methods=["GET", "POST"])
    @login_required
    def new_grade():
        if request.method == "POST":
            course = request.form.get("course", "").strip()
            credits = request.form.get("credits", "").strip()
            grade_value = request.form.get("grade", "").strip().upper()

            if not course or not credits or not grade_value:
                flash("Please complete all grade fields.", "warning")
            else:
                try:
                    credits_value = float(credits)
                    if credits_value <= 0:
                        raise ValueError
                    if grade_value not in GRADE_POINTS:
                        raise ValueError
                except ValueError:
                    flash("Enter a valid grade and credit value.", "danger")
                else:
                    record = Grade(
                        user_id=current_user.id,
                        course=course,
                        credits=credits_value,
                        grade=grade_value,
                    )
                    db.session.add(record)
                    db.session.commit()
                    flash("Grade recorded successfully.", "success")
                    return redirect(url_for("grades"))

        return render_template("grade_form.html", grade=None)

    @app.route("/grades/<int:grade_id>/delete", methods=["POST"])
    @login_required
    def delete_grade(grade_id):
        grade = Grade.query.filter_by(id=grade_id, user_id=current_user.id).first_or_404()
        db.session.delete(grade)
        db.session.commit()
        flash("Grade deleted.", "info")
        return redirect(url_for("grades"))

    @app.route("/calendar-events")
    @login_required
    def calendar_events():
        events = [
            {
                "title": task.title,
                "due_date": task.due_date.isoformat() if task.due_date else "",
                "priority": task.priority,
                "status": task.status,
            }
            for task in Task.query.filter_by(user_id=current_user.id).all()
            if task.due_date
        ]
        return jsonify(events)

    @app.template_filter("format_date")
    def format_date(value):
        return value.strftime("%Y-%m-%d") if value else ""

    @app.route("/api/stats")
    @login_required
    def api_stats():
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        grades = Grade.query.filter_by(user_id=current_user.id).all()
        completed = sum(1 for t in tasks if t.status.lower() == "completed")
        today = datetime.now(timezone.utc).date()
        overdue = sum(
            1 for t in tasks
            if t.due_date and t.due_date < today and t.status.lower() != "completed"
        )
        gpa_val = calculate_gpa(grades)
        return jsonify({
            "total_tasks": len(tasks),
            "completed_tasks": completed,
            "pending_tasks": len(tasks) - completed,
            "overdue_tasks": overdue,
            "gpa": gpa_val,
            "courses_recorded": len(grades),
            "academic_standing": get_academic_standing(gpa_val, len(grades)),
        })

    @app.route("/api/tasks/upcoming")
    @login_required
    def api_tasks_upcoming():
        try:
            days = max(1, min(90, int(request.args.get("days", 7))))
        except ValueError:
            days = 7
        today = datetime.now(timezone.utc).date()
        horizon = today + timedelta(days=days)
        tasks = (
            Task.query.filter_by(user_id=current_user.id)
            .order_by(Task.due_date.asc())
            .all()
        )
        upcoming_items = [
            {
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.isoformat(),
                "priority": t.priority,
                "status": t.status,
            }
            for t in tasks
            if t.due_date and today <= t.due_date <= horizon and t.status.lower() != "completed"
        ]
        return jsonify({"window_days": days, "count": len(upcoming_items), "tasks": upcoming_items})

    return app

GRADE_POINTS = {
    "A+": 4.0,
    "A": 4.0,
    "A-": 3.7,
    "B+": 3.3,
    "B": 3.0,
    "B-": 2.7,
    "C+": 2.3,
    "C": 2.0,
    "C-": 1.7,
    "D+": 1.3,
    "D": 1.0,
    "F": 0.0,
}

if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
