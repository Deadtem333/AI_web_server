import os
import subprocess
import sys
import time
import signal
import atexit
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_python_executable():
    candidates = [
        Path(sys.executable),
        ROOT / "venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / "venv" / "bin" / "python",
        ROOT / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def check_paths():
    if not (ROOT / "app" / "main.py").exists():
        print("app/main.py not found")
        sys.exit(1)
    if not (ROOT / "frontend" / "app.py").exists():
        print("frontend/app.py not found")
        sys.exit(1)
    print("Files found, continuing")


def kill_processes():
    # Убиваем все uvicorn и streamlit процессы
    subprocess.run(["pkill", "-f", "uvicorn"], check=False)
    subprocess.run(["pkill", "-f", "streamlit"], check=False)
    # Освобождаем порт 8081
    try:
        subprocess.run(["fuser", "-k", "8081/tcp"], check=False, capture_output=True)
    except FileNotFoundError:
        try:
            output = subprocess.check_output(["lsof", "-t", "-i:8081"], text=True)
            for pid in output.strip().split():
                os.kill(int(pid), signal.SIGKILL)
        except Exception:
            pass
    time.sleep(2)


def run_backend(python_exe):
    print("Starting backend on port 8081")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"],
        cwd=str(ROOT),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
        start_new_session=True,
    )


def run_frontend(python_exe):
    print("Starting frontend on port 8501 (default for Streamlit Cloud)")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", "frontend/app.py",
         "--server.port", "8501",
         "--server.address", "0.0.0.0",
         "--server.headless", "true"],
        cwd=str(ROOT),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
        start_new_session=True,
    )


def cleanup():
    print("Stopping services...")
    kill_processes()


if __name__ == "__main__":
    kill_processes()

    print("=== Project structure check ===")
    check_paths()

    python_exe = find_python_executable()
    print(f"Using Python: {python_exe}")

    print("=== Starting services ===")
    backend = run_backend(python_exe)
    time.sleep(5)
    frontend = run_frontend(python_exe)

    atexit.register(cleanup)
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())

    print("All services running")
    print("Backend (internal) -> http://localhost:8081")
    print("Frontend -> https://<your-app>.streamlit.app")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        cleanup()