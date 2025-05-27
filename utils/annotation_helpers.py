import os
import json

SESSION_DIR = "sessions"

def load_session(user_id):
    path = os.path.join(SESSION_DIR, f"{user_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_session(user_id, session_data):
    os.makedirs(SESSION_DIR, exist_ok=True)
    path = os.path.join(SESSION_DIR, f"{user_id}.json")
    with open(path, "w") as f:
        json.dump(session_data, f, indent=2)
