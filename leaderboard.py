from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from datetime import datetime
import asyncio

app = FastAPI(
    title="CyberHunt Admin Backend",
    description="Admin APIs for CyberHunt",
    version="1.0.0"
)


# -----------------------------
# Leaderboard Response Model
# -----------------------------

class LeaderboardEntry(BaseModel):
    rank: int
    participant_name: str
    score: int
    challenges_solved: int
    last_submission_time: datetime


# -----------------------------
# Temporary Participant Data
# -----------------------------

def get_participant_data():
    """
    Temporary data source.

    Later, replace this function with
    the actual database query.
    """

    return [
        {
            "participant_name": "Ayushi",
            "score": 500,
            "challenges_solved": 4,
            "last_submission_time": datetime(2026, 9, 16, 19, 30)
        },
        {
            "participant_name": "Riya",
            "score": 750,
            "challenges_solved": 6,
            "last_submission_time": datetime(2026, 9, 16, 19, 25)
        },
        {
            "participant_name": "Aman",
            "score": 500,
            "challenges_solved": 3,
            "last_submission_time": datetime(2026, 9, 16, 19, 20)
        },
        {
            "participant_name": "Rahul",
            "score": 600,
            "challenges_solved": 5,
            "last_submission_time": datetime(2026, 9, 16, 19, 28)
        }
    ]


# -----------------------------
# Generate Leaderboard
# -----------------------------

def generate_leaderboard():

    participants = get_participant_data()

    # Higher score comes first.
    # If score is same, earlier submission time comes first.

    sorted_participants = sorted(
        participants,
        key=lambda participant: (
            -participant["score"],
            participant["last_submission_time"]
        )
    )

    leaderboard = []

    for index, participant in enumerate(sorted_participants):

        leaderboard.append(
            {
                "rank": index + 1,
                "participant_name": participant["participant_name"],
                "score": participant["score"],
                "challenges_solved": participant["challenges_solved"],
                "last_submission_time": participant["last_submission_time"]
            }
        )

    return leaderboard


# -----------------------------
# Home
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "CyberHunt Admin Backend is running!"
    }


# -----------------------------
# Leaderboard API
# -----------------------------

@app.get(
    "/admin/leaderboard",
    response_model=list[LeaderboardEntry]
)
def get_leaderboard():

    return generate_leaderboard()


# -----------------------------
# Leaderboard WebSocket
# -----------------------------

@app.websocket("/ws/leaderboard")
async def leaderboard_websocket(websocket: WebSocket):

    await websocket.accept()

    try:
        while True:

            leaderboard = generate_leaderboard()

            await websocket.send_json(leaderboard)

            await asyncio.sleep(2)

    except WebSocketDisconnect:

        print("Leaderboard client disconnected")