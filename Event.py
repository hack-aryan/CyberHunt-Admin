from fastapi import FastAPI, HTTPException
from datetime import datetime

app = FastAPI(title="Event Management API")

EVENT_DURATION_SECONDS = 2 * 60 * 60

event = {
    "status": "IDLE",
    "started_at": None,
    "duration_seconds": EVENT_DURATION_SECONDS,
    "time_remaining_seconds": EVENT_DURATION_SECONDS,
    "updated_at": datetime.now().isoformat()
}

@app.get("/")
def home():
    return {"message": "Event Management Backend is running!"}

@app.get("/admin/event/status")
def get_event_status():
    return {"message": "Event status retrieved successfully", "event": event}

@app.post("/admin/event/start")
def start_event():
    if event["status"] != "IDLE":
        raise HTTPException(status_code=400, detail="Event can only be started from IDLE state")
    event["status"] = "RUNNING"
    event["started_at"] = datetime.now().isoformat()
    event["updated_at"] = datetime.now().isoformat()
    return {"message": "Event started successfully", "event": event}

@app.post("/admin/event/pause")
def pause_event():
    if event["status"] != "RUNNING":
        raise HTTPException(status_code=400, detail="Event can only be paused while RUNNING")
    event["status"] = "PAUSED"
    event["updated_at"] = datetime.now().isoformat()
    return {"message": "Event paused successfully", "event": event}

@app.post("/admin/event/resume")
def resume_event():
    if event["status"] != "PAUSED":
        raise HTTPException(status_code=400, detail="Event can only be resumed from PAUSED state")
    event["status"] = "RUNNING"
    event["updated_at"] = datetime.now().isoformat()
    return {"message": "Event resumed successfully", "event": event}

@app.post("/admin/event/end")
def end_event():
    if event["status"] not in ["RUNNING", "PAUSED"]:
        raise HTTPException(status_code=400, detail="Event can only be ended while RUNNING or PAUSED")
    event["status"] = "ENDED"
    event["updated_at"] = datetime.now().isoformat()
    return {"message": "Event ended successfully", "event": event}

@app.post("/admin/event/reset")
def reset_event():
    event["status"] = "IDLE"
    event["started_at"] = None
    event["duration_seconds"] = EVENT_DURATION_SECONDS
    event["time_remaining_seconds"] = EVENT_DURATION_SECONDS
    event["updated_at"] = datetime.now().isoformat()
    return {"message": "Event reset successfully", "event": event}
