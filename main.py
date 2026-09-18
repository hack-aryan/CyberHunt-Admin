from datetime import datetime, timezone
from typing import Optional
import asyncio
import json

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import get_connection, init_db

app = FastAPI(title="CyberHunt Admin API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://127.0.0.1:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChallengeIn(BaseModel):
    title: str
    description: str
    flag: str
    points: int = Field(ge=0)
    hint: Optional[str] = ""
    category: str
    dependency: Optional[str] = "None"

class AnnouncementIn(BaseModel):
    message: str

class StatusIn(BaseModel):
    status: str

@app.on_event("startup")
def startup():
    init_db()


def now():
    return datetime.now(timezone.utc).isoformat()


def event_row(conn):
    row = conn.execute("SELECT * FROM Event ORDER BY id LIMIT 1").fetchone()
    if not row:
        conn.execute("INSERT INTO Event(name,status,duration_seconds,remaining_seconds) VALUES(?,?,?,?)", ("CyberHunt Event", "IDLE", 7200, 7200))
        conn.commit()
        row = conn.execute("SELECT * FROM Event ORDER BY id LIMIT 1").fetchone()
    return row


def event_payload(row):
    d = dict(row)
    remaining = int(d.get("remaining_seconds", d.get("duration_seconds", 14400)))
    if d["status"] == "RUNNING" and d.get("started_at"):
        started = datetime.fromisoformat(d["started_at"])
        remaining = max(0, remaining - int((datetime.now(timezone.utc) - started).total_seconds()))
    if d["status"] == "ENDED":
        remaining = 0
    d["time_remaining_seconds"] = remaining
    return d


def record_event_announcement(conn, title: str, message: str):
    """Store event-control updates so they are visible in the admin announcement feed."""
    conn.execute("INSERT INTO Announcement(message) VALUES(?)", (f"{title}: {message}",))

@app.get("/")
def home():
    return {"message": "CyberHunt Admin Backend is running!"}

# Event management
@app.get("/admin/event/status")
def get_event_status():
    conn = get_connection()
    try:
        return {"message": "Event status retrieved successfully", "event": event_payload(event_row(conn))}
    finally: conn.close()

@app.post("/admin/event/start")
def start_event():
    conn = get_connection()
    try:
        row = event_row(conn)
        if row["status"] != "IDLE":
            raise HTTPException(400, "Event can only be started from IDLE state")
        t = now()
        conn.execute("UPDATE Event SET status='RUNNING', started_at=?, paused_at=NULL, ended_at=NULL, remaining_seconds=duration_seconds, updated_at=? WHERE id=?", (t,t,row["id"]))
        record_event_announcement(conn, "Event Started", "The CyberHunt event is now live.")
        conn.commit()
        return {"message":"Event started successfully", "event":event_payload(event_row(conn))}
    finally: conn.close()

@app.post("/admin/event/pause")
def pause_event():
    conn = get_connection()
    try:
        row = event_row(conn)
        if row["status"] != "RUNNING": raise HTTPException(400, "Event can only be paused while RUNNING")
        t = now(); remaining = event_payload(row)["time_remaining_seconds"]; conn.execute("UPDATE Event SET status='PAUSED', paused_at=?, remaining_seconds=?, updated_at=? WHERE id=?", (t,remaining,t,row["id"])); record_event_announcement(conn, "Event Paused", "The CyberHunt event is temporarily paused.")
        conn.commit(); return {"message":"Event paused successfully", "event":event_payload(event_row(conn))}
    finally: conn.close()

@app.post("/admin/event/resume")
def resume_event():
    conn = get_connection()
    try:
        row = event_row(conn)
        if row["status"] != "PAUSED": raise HTTPException(400, "Event can only be resumed from PAUSED state")
        t = now(); conn.execute("UPDATE Event SET status='RUNNING', started_at=?, updated_at=? WHERE id=?", (t,t,row["id"])); record_event_announcement(conn, "Event Resumed", "The CyberHunt event has resumed.")
        conn.commit(); return {"message":"Event resumed successfully", "event":event_payload(event_row(conn))}
    finally: conn.close()

@app.post("/admin/event/end")
def end_event():
    conn = get_connection()
    try:
        row = event_row(conn)
        if row["status"] not in ("RUNNING","PAUSED"): raise HTTPException(400, "Event can only be ended while RUNNING or PAUSED")
        t = now(); remaining = event_payload(row)["time_remaining_seconds"]; conn.execute("UPDATE Event SET status='ENDED', ended_at=?, remaining_seconds=?, updated_at=? WHERE id=?", (t,remaining,t,row["id"])); record_event_announcement(conn, "Event Ended", "The CyberHunt event has ended.")
        conn.commit(); return {"message":"Event ended successfully", "event":event_payload(event_row(conn))}
    finally: conn.close()

@app.post("/admin/event/reset")
def reset_event():
    conn = get_connection()
    try:
        row = event_row(conn); t = now()
        conn.execute(
            "UPDATE Event SET status='IDLE', started_at=NULL, paused_at=NULL, ended_at=NULL, duration_seconds=7200, remaining_seconds=7200, updated_at=? WHERE id=?",
            (t, row["id"])
        )
        record_event_announcement(conn, "Event Reset", "The event timer was reset to 2 hours.")
        conn.commit()
        return {"message":"Event reset successfully to 2 hours", "event":event_payload(event_row(conn))}
    finally:
        conn.close()

# Challenges
@app.get("/admin/challenges")
def get_challenges():
    conn=get_connection()
    try:
        rows=conn.execute("""SELECT c.*, COALESCE(GROUP_CONCAT(d.dependency_challenge_id), '') dependency_ids
          FROM Challenge c LEFT JOIN ChallengeDependency d ON d.challenge_id=c.id GROUP BY c.id ORDER BY c.id""").fetchall()
        data=[]
        for r in rows:
            x=dict(r); x["dependency"] = x.pop("dependency_ids") or "None"; data.append(x)
        return {"message":"Challenges retrieved successfully", "total_challenges":len(data), "challenges":data}
    finally: conn.close()

@app.post("/admin/challenges")
def create_challenge(challenge: ChallengeIn):
    conn=get_connection()
    try:
        cur=conn.execute("INSERT INTO Challenge(title,description,flag,points,hint,category) VALUES(?,?,?,?,?,?)", (challenge.title, challenge.description, challenge.flag, challenge.points, challenge.hint or "", challenge.category))
        cid=cur.lastrowid
        dep=challenge.dependency
        if dep and dep != "None":
            try: dep_id=int(str(dep).split()[-1])
            except ValueError: dep_id=None
            if dep_id: conn.execute("INSERT OR IGNORE INTO ChallengeDependency(challenge_id,dependency_challenge_id) VALUES(?,?)",(cid,dep_id))
        conn.commit(); row=conn.execute("SELECT * FROM Challenge WHERE id=?",(cid,)).fetchone()
        return {"message":"Challenge created successfully", "challenge":dict(row)}
    finally: conn.close()

@app.put("/admin/challenges/{challenge_id}")
def update_challenge(challenge_id:int, challenge:ChallengeIn):
    conn=get_connection()
    try:
        if not conn.execute("SELECT id FROM Challenge WHERE id=?",(challenge_id,)).fetchone(): raise HTTPException(404,"Challenge not found")
        conn.execute("UPDATE Challenge SET title=?,description=?,flag=?,points=?,hint=?,category=?,updated_at=? WHERE id=?", (challenge.title, challenge.description, challenge.flag, challenge.points, challenge.hint or "", challenge.category, now(), challenge_id))
        conn.execute("DELETE FROM ChallengeDependency WHERE challenge_id=?",(challenge_id,))
        if challenge.dependency and challenge.dependency != "None":
            try: dep_id=int(str(challenge.dependency).split()[-1])
            except ValueError: dep_id=None
            if dep_id: conn.execute("INSERT OR IGNORE INTO ChallengeDependency(challenge_id,dependency_challenge_id) VALUES(?,?)",(challenge_id,dep_id))
        conn.commit(); row=conn.execute("SELECT * FROM Challenge WHERE id=?",(challenge_id,)).fetchone()
        return {"message":"Challenge updated successfully", "challenge":dict(row)}
    finally: conn.close()

@app.delete("/admin/challenges/{challenge_id}")
def delete_challenge(challenge_id:int):
    conn=get_connection()
    try:
        cur=conn.execute("DELETE FROM Challenge WHERE id=?",(challenge_id,)); conn.commit()
        if cur.rowcount == 0: raise HTTPException(404,"Challenge not found")
        return {"message":"Challenge deleted successfully", "challenge_id":challenge_id}
    finally: conn.close()

# Announcements
@app.post("/admin/announcements")
def create_announcement(data: AnnouncementIn):
    conn=get_connection()
    try:
        cur=conn.execute("INSERT INTO Announcement(message) VALUES(?)",(data.message,)); conn.commit()
        row=conn.execute("SELECT * FROM Announcement WHERE id=?",(cur.lastrowid,)).fetchone()
        return {"message":"Announcement created successfully", "announcement":dict(row)}
    finally: conn.close()

@app.get("/admin/announcements")
def get_announcements():
    conn=get_connection()
    try:
        rows=conn.execute("SELECT * FROM Announcement ORDER BY created_at DESC,id DESC").fetchall()
        return {"message":"Announcements retrieved successfully", "announcements":[dict(r) for r in rows]}
    finally: conn.close()

# Participants
@app.get("/admin/participants")
def get_participants():
    conn=get_connection()
    try:
        rows=conn.execute("""SELECT p.*, u.username name, c.title current_challenge
          FROM Participant p JOIN User u ON u.id=p.user_id LEFT JOIN Challenge c ON c.id=p.current_challenge_id ORDER BY p.id""").fetchall()
        data=[]
        for r in rows:
            x=dict(r); data.append(x)
        return {"message":"Participants retrieved successfully", "total_participants":len(data), "participants":data}
    finally: conn.close()

@app.get("/admin/participants/{participant_id}")
def get_participant(participant_id:int):
    conn=get_connection()
    try:
        row=conn.execute("""SELECT p.*,u.username name,c.title current_challenge FROM Participant p JOIN User u ON u.id=p.user_id LEFT JOIN Challenge c ON c.id=p.current_challenge_id WHERE p.id=?""",(participant_id,)).fetchone()
        if not row: raise HTTPException(404,"Participant not found")
        history=conn.execute("""SELECT c.title challenge,s.submitted_at,s.result,s.score_awarded score FROM Submission s JOIN Challenge c ON c.id=s.challenge_id WHERE s.participant_id=? ORDER BY s.submitted_at""",(participant_id,)).fetchall()
        x=dict(row); x["submission_history"]=[dict(h) for h in history]
        return {"message":"Participant retrieved successfully", "participant":x}
    finally: conn.close()

@app.get("/admin/participants/{participant_id}/submissions")
def get_submission_history(participant_id:int):
    conn=get_connection()
    try:
        if not conn.execute("SELECT id FROM Participant WHERE id=?",(participant_id,)).fetchone(): raise HTTPException(404,"Participant not found")
        rows=conn.execute("SELECT * FROM Submission WHERE participant_id=? ORDER BY submitted_at",(participant_id,)).fetchall()
        return {"participant_id":participant_id,"submission_history":[dict(r) for r in rows]}
    finally: conn.close()

@app.get("/admin/participants/{participant_id}/activity")
def get_participant_activity(participant_id:int):
    conn=get_connection()
    try:
        row=conn.execute("""SELECT p.status,p.last_activity,u.username name,c.title current_challenge FROM Participant p JOIN User u ON u.id=p.user_id LEFT JOIN Challenge c ON c.id=p.current_challenge_id WHERE p.id=?""",(participant_id,)).fetchone()
        if not row: raise HTTPException(404,"Participant not found")
        return {"participant_id":participant_id,**dict(row)}
    finally: conn.close()

@app.post("/admin/participants/{participant_id}/status")
def update_participant_status(participant_id:int, data:StatusIn):
    if data.status not in ("active","idle","offline"): raise HTTPException(400,"Invalid status")
    conn=get_connection()
    try:
        cur=conn.execute("UPDATE Participant SET status=?,last_activity=? WHERE id=?",(data.status,now(),participant_id)); conn.commit()
        if cur.rowcount==0: raise HTTPException(404,"Participant not found")
        row=conn.execute("SELECT * FROM Participant WHERE id=?",(participant_id,)).fetchone()
        return {"message":"Participant status updated","participant":dict(row)}
    finally: conn.close()

# Leaderboard

def leaderboard_data():
    conn=get_connection()
    try:
        rows=conn.execute("""SELECT p.id,u.username participant_name,p.total_score score,p.solved_challenges challenges_solved,
          COALESCE(MAX(s.submitted_at), p.last_activity, p.joined_at) last_submission_time
          FROM Participant p JOIN User u ON u.id=p.user_id LEFT JOIN Submission s ON s.participant_id=p.id
          GROUP BY p.id ORDER BY p.total_score DESC,last_submission_time ASC""").fetchall()
        return [{**dict(r),"rank":i+1} for i,r in enumerate(rows)]
    finally: conn.close()

@app.get("/admin/leaderboard")
def get_leaderboard(): return leaderboard_data()

@app.websocket("/ws/leaderboard")
async def leaderboard_websocket(websocket:WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(leaderboard_data())
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
