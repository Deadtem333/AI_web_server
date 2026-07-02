import os
import subprocess
import sys
import time
import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def port_free(port: int) -> bool:
    """Проверяем, свободен ли порт."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("0.0.0.0", port)) != 0


def kill_python_processes():
    """Убиваем uvicorn и streamlit через psutil."""
    try:
        import psutil
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(proc.info["cmdline"])
            if "uvicorn" in cmd or "streamlit" in cmd:
                print(f"Killing {proc.pid}: {cmd}")
                proc.kill()
        except Exception:
            pass


def run_backend(python_exe):
    if not port_free(8081):
        print("⚠️ Backend port 8081 already in use — NOT starting second backend")
        return None

    print("🚀 Starting backend on port 8081")
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", "8081"],
        cwd=str(ROOT),
        start_new_session=True
    )


def run_frontend(python_exe):
    print("🚀 Starting Streamlit frontend (auto-port)")
    return subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", "frontend/app.py",
         "--server.address", "0.0.0.0",
         "--server.headless", "true"],
        cwd=str(ROOT),
        start_new_session=True
    )


if __name__ == "__main__":
    print("🔪 Killing old processes...")
    kill_python_processes()

    python_exe = sys.executable
    print(f"Using Python: {python_exe}")

    print("🚀 Launching backend...")
    backend = run_backend(python_exe)

    time.sleep(3)

    print("🚀 Launching frontend...")
    frontend = run_frontend(python_exe)

    print("✅ All services started")
    print("Backend → http://localhost:8081")
    print("Frontend → Streamlit chooses free port automatically")
