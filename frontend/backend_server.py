import threading
import uvicorn
from app.main import app

def start_backend():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def run_in_background():
    thread = threading.Thread(target=start_backend, daemon=True)
    thread.start()
