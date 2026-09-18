from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Challenge Management API")

class Challenge(BaseModel):
    title: str
    description: str
    flag: str
    points: int
    hint: Optional[str] = ""
    category: str
    dependency: Optional[str] = "None"

challenges = [
    {"id": 1, "title": "Hidden Message", "description": "Find the hidden message in the provided data.", "flag": "FLAG{hidden_message}", "points": 100, "hint": "Look carefully at the encoded data.", "category": "Cryptography", "dependency": "None"},
    {"id": 2, "title": "Web Detective", "description": "Find the vulnerability in the given web application.", "flag": "FLAG{web_detective}", "points": 150, "hint": "Inspect how user input is handled.", "category": "Web Security", "dependency": "Challenge 1"},
    {"id": 3, "title": "Packet Hunter", "description": "Analyze the network traffic and identify the hidden information.", "flag": "FLAG{packet_hunter}", "points": 200, "hint": "Check the network packets carefully.", "category": "Network Security", "dependency": "Challenge 2"}
]

@app.get("/admin/challenges")
def get_challenges():
    return {"message": "Challenges retrieved successfully", "total_challenges": len(challenges), "challenges": challenges}

@app.post("/admin/challenges")
def create_challenge(challenge: Challenge):
    new_id = max((c["id"] for c in challenges), default=0) + 1
    new_challenge = {"id": new_id, **challenge.model_dump()}
    challenges.append(new_challenge)
    return {"message": "Challenge created successfully", "challenge": new_challenge}

@app.put("/admin/challenges/{challenge_id}")
def update_challenge(challenge_id: int, challenge: Challenge):
    for existing_challenge in challenges:
        if existing_challenge["id"] == challenge_id:
            existing_challenge.update(challenge.model_dump())
            return {"message": "Challenge updated successfully", "challenge": existing_challenge}
    raise HTTPException(status_code=404, detail="Challenge not found")

@app.delete("/admin/challenges/{challenge_id}")
def delete_challenge(challenge_id: int):
    for challenge in challenges:
        if challenge["id"] == challenge_id:
            challenges.remove(challenge)
            return {"message": "Challenge deleted successfully", "challenge_id": challenge_id}
    raise HTTPException(status_code=404, detail="Challenge not found")
