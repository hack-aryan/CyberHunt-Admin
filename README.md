# CyberHunt Admin — Full Stack MVP

## Start everything on Windows

Double-click `start_cyberhunt.bat` to start the backend first on port **8000** and the frontend on port **4000** in separate terminal windows.

Backend: http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs
Frontend: http://127.0.0.1:4000


## Run backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
It has a file main.py which contains combined code for backend, I have also created a folder "Codes" for seprate function code 

## Run frontend (separate port)

In another terminal:

```bash
cd frontend
python -m http.server 4000
```

The frontend calls the FastAPI backend over HTTP and the leaderboard uses the WebSocket endpoint.

## Database

The included `database/cyberhunt.db` is a dummy SQLite database for integration testing. It is not the production database. Set `DATABASE_PATH` when replacing it with another SQLite file.

Tables:
- User
- Event
- Challenge
- ChallengeDependency
- Announcement
- Participant
- Submission
- ScoreTransaction

## API areas

- Event: start, pause, resume, end, reset, status
- Challenges: list, create, update, delete
- Announcements: list, create
- Participants: list, details, submissions, activity, status
- Leaderboard: REST + WebSocket

### Event reset
The Dashboard and Event Management pages include **Reset to 2 Hours**. `POST /admin/event/reset` restores the backend-controlled event timer to **7200 seconds (2 hours)** and sets the event to `IDLE`.
