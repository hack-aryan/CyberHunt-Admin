from fastapi import FastAPI, HTTPException
from datetime import datetime

app = FastAPI(title="Participant Monitoring API")

participants = [
    {"id": 101, "name": "Participant 101", "current_challenge": "Web Security - Challenge 3", "total_score": 850, "solved_challenges": 7, "hints_used": 2, "status": "active", "last_activity": "2026-09-16T21:42:10", "submission_history": [
        {"challenge": "Web Security - Challenge 1", "submitted_at": "2026-09-16T20:15:22", "result": "accepted", "score": 100},
        {"challenge": "Web Security - Challenge 2", "submitted_at": "2026-09-16T20:48:11", "result": "accepted", "score": 150},
        {"challenge": "Web Security - Challenge 3", "submitted_at": "2026-09-16T21:20:05", "result": "wrong", "score": 0}
    ]},
    {"id": 102, "name": "Participant 102", "current_challenge": "Cryptography - Challenge 2", "total_score": 620, "solved_challenges": 5, "hints_used": 4, "status": "active", "last_activity": "2026-09-16T21:38:40", "submission_history": [
        {"challenge": "Cryptography - Challenge 1", "submitted_at": "2026-09-16T19:10:30", "result": "accepted", "score": 120},
        {"challenge": "Cryptography - Challenge 2", "submitted_at": "2026-09-16T21:05:15", "result": "wrong", "score": 0}
    ]},
    {"id": 103, "name": "Participant 103", "current_challenge": "Network Security - Challenge 1", "total_score": 400, "solved_challenges": 3, "hints_used": 1, "status": "idle", "last_activity": "2026-09-16T20:55:12", "submission_history": [
        {"challenge": "Network Security - Challenge 1", "submitted_at": "2026-09-16T20:30:00", "result": "accepted", "score": 200}
    ]}
]

@app.get("/admin/participants")
def get_participants():
    return {"message": "Participants retrieved successfully", "total_participants": len(participants), "participants": participants}

@app.get("/admin/participants/{participant_id}")
def get_participant(participant_id: int):
    for participant in participants:
        if participant["id"] == participant_id:
            return {"message": "Participant retrieved successfully", "participant": participant}
    raise HTTPException(status_code=404, detail="Participant not found")

@app.get("/admin/participants/{participant_id}/submissions")
def get_submission_history(participant_id: int):
    for participant in participants:
        if participant["id"] == participant_id:
            return {"participant_id": participant_id, "submission_history": participant["submission_history"]}
    raise HTTPException(status_code=404, detail="Participant not found")

@app.get("/admin/participants/{participant_id}/activity")
def get_participant_activity(participant_id: int):
    for participant in participants:
        if participant["id"] == participant_id:
            return {"participant_id": participant_id, "name": participant["name"], "status": participant["status"], "current_challenge": participant["current_challenge"], "last_activity": participant["last_activity"]}
    raise HTTPException(status_code=404, detail="Participant not found")

@app.post("/admin/participants/{participant_id}/status")
def update_participant_status(participant_id: int, status: str):
    allowed_status = ["active", "idle", "offline"]
    if status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid status")
    for participant in participants:
        if participant["id"] == participant_id:
            participant["status"] = status
            participant["last_activity"] = datetime.now().isoformat()
            return {"message": "Participant status updated", "participant": participant}
    raise HTTPException(status_code=404, detail="Participant not found")
