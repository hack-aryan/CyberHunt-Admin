from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Announcement Management API")
announcements = []

class Announcement(BaseModel):
    message: str

@app.post("/admin/announcements")
def create_announcement(announcement: Announcement):
    new_announcement = {
        "id": len(announcements) + 1,
        "message": announcement.message,
        "created_at": datetime.now().isoformat(),
    }
    announcements.append(new_announcement)
    return {
        "message": "Announcement created successfully",
        "announcement": new_announcement,
    }

@app.get("/admin/announcements")
def get_announcements():
    return {
        "message": "Announcements retrieved successfully",
        "announcements": announcements,
    }
