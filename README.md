# smart-student-planner

A productivity-focused student planner built with Flask and SQLite. This app helps students manage assignments, deadlines, study sessions, GPA tracking, and reminders using a clean UI and a lightweight local database.

## Features

- Login and registration system
- Add / edit / delete tasks
- Priority labels for tasks
- Due-date reminders and upcoming task highlights
- GPA tracking with credit-weighted grades
- Simple calendar-style event view for deadlines
- Dark mode toggle with local browser persistence
- Local SQLite database for storage

## Tech Stack

- Python 3
- Flask
- Flask-Login
- Flask-SQLAlchemy
- SQLite
- HTML, CSS, JavaScript

## Project Structure

- `app.py` — Flask app and route definitions
- `models.py` — SQLAlchemy models for users, tasks, and grades
- `config.py` — application configuration
- `templates/` — HTML templates
- `static/` — CSS and JavaScript files
- `requirements.txt` — Python dependencies

## Setup Instructions

1. Create and activate a Python virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the application:

```powershell
python app.py
```

4. Open the app in your browser:

```text
http://127.0.0.1:5000
```

## GitHub Repository Setup

1. Initialize the repository locally if it is not already initialized:

```powershell
git init
```

2. Add all files and commit:

```powershell
git add .
git commit -m "Initial student planner app"
```

3. Create a new GitHub repository named `smart-student-planner`.

4. Connect the local repository to GitHub:

```powershell
git remote add origin https://github.com/<your-username>/smart-student-planner.git
```

5. Push the project to GitHub:

```powershell
git branch -M main
git push -u origin main
```

## Notes

- The database file is stored in `instance/planner.db` and is ignored by Git.
- Change `SECRET_KEY` in `config.py` or set `SECRET_KEY` in your environment for a production deployment.
- Use the dark mode toggle in the app header to switch themes.
