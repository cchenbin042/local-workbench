import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


def test_cli_help_and_rejects_invalid_bind():
    help_result = subprocess.run([sys.executable, "-m", "workbench", "--help"], capture_output=True, text=True, timeout=10)
    assert help_result.returncode == 0
    assert "--app-root" in help_result.stdout
    for args in [["--host", "0.0.0.0"], ["--port", "0"], ["--port", "65536"]]:
        result = subprocess.run([sys.executable, "-m", "workbench", *args], capture_output=True, text=True, timeout=10)
        assert result.returncode == 2


def test_real_server_starts_without_model(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = {key: value for key, value in os.environ.items() if key != "WORKBENCH_API_KEY"}
    with (tmp_path / "server.log").open("w+", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "-m", "workbench", "--port", str(port), "--app-root", str(tmp_path)], stdout=log, stderr=log, env=env)
        try:
            deadline = time.monotonic() + 15
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=1) as client:
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        log.seek(0)
                        raise AssertionError(log.read())
                    try:
                        response = client.get("/api/health")
                    except (httpx.ConnectError, httpx.TimeoutException):
                        time.sleep(0.1)
                        continue
                    assert response.status_code == 200
                    assert response.json() == {"status": "ok"}
                    assert client.get("/api/health", headers={"Origin": "https://evil.test"}).status_code == 403
                    assert "/api/health" in client.get("/openapi.json").json()["paths"]
                    assert not (tmp_path / ".local-workbench").exists()
                    return
            log.seek(0)
            raise AssertionError(f"Server did not become healthy within 15 seconds:\n{log.read()}")
        finally:
            process.terminate()
            process.wait(timeout=10)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell startup integration")
def test_powershell_script_starts_from_other_directory(tmp_path):
    root = Path(__file__).resolve().parents[2]
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with (tmp_path / "powershell.log").open("w+b") as log:
        process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(root / "scripts/start-backend.ps1"), "-Port", str(port)],
            cwd=tmp_path, stdout=log, stderr=log, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            deadline = time.monotonic() + 20
            with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=1) as client:
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        log.seek(0)
                        raise AssertionError(log.read().decode("utf-8", errors="replace"))
                    try:
                        response = client.get("/api/health")
                    except (httpx.ConnectError, httpx.TimeoutException):
                        time.sleep(0.1)
                        continue
                    assert response.status_code == 200 and response.json() == {"status": "ok"}
                    return
            log.seek(0)
            raise AssertionError(f"PowerShell script did not start a healthy service:\n{log.read().decode('utf-8', errors='replace')}")
        finally:
            if process.poll() is None:
                # Kill only the process tree created by this test, including its Python child.
                subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"], check=True, stdout=subprocess.DEVNULL)
            process.wait(timeout=10)
