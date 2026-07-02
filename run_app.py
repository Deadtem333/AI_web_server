import os
import subprocess
import sys
import time
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
        print("Файл app/main.py не найден!")
        sys.exit(1)

    if not (ROOT / "frontend" / "app.py").exists():
        print("Файл frontend/app.py не найден!")
        sys.exit(1)

    print("Файлы найдены, продолжаем...")


def run_backend(python_exe):
    print("Запуск backend на порту 8081...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"],
        cwd=str(ROOT),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def run_frontend(python_exe):
    print("▶ Запуск frontend на порту 8501 (стандартный для Streamlit Cloud)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    return subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", "frontend/app.py", "--server.headless", "true"],
        cwd=str(ROOT),
        env=env,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


if __name__ == "__main__":
    print("=== Проверка структуры проекта ===")
    check_paths()

    python_exe = find_python_executable()
    print(f"Используем Python: {python_exe}")

    print("=== Запуск сервисов ===")
    backend = run_backend(python_exe)
    time.sleep(3)  # Даём бэкенду время инициализироваться
    frontend = run_frontend(python_exe)

    print("\nВсё запущено!")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nОстановка...")
        backend.terminate()
        frontend.terminate()