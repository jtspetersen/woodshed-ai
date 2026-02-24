# Woodshed AI — Development Launcher
# Copyright (C) 2026 Josh Petersen
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Usage:
#   python dev.py          Start all services
#   python dev.py stop     Stop any running services
#   python dev.py status   Show which services are running
#
# PID file: .dev.pids (written on start, read on stop)

import json
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent
PID_FILE = ROOT_DIR / ".dev.pids"

# Default preferred ports (used if available, otherwise auto-detect)
DEFAULT_PORTS = {
    "transcription": 8765,
    "backend": 8000,
    "frontend": 3001,
}

# ANSI color codes
C_CYAN = "\033[36m"
C_YELLOW = "\033[33m"
C_MAGENTA = "\033[35m"
C_GREEN = "\033[32m"
C_RED = "\033[31m"
C_RESET = "\033[0m"
C_BOLD = "\033[1m"

SERVICE_COLORS = {
    "transcription": C_CYAN,
    "backend": C_YELLOW,
    "frontend": C_MAGENTA,
}


# ──────────────────────────────────────────────
#  Port detection
# ──────────────────────────────────────────────

def _is_port_available(port: int) -> bool:
    """Check if a TCP port is available to bind."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _find_open_port(preferred: int, range_start: int = 3000, range_end: int = 9999) -> int:
    """Find an open port, trying the preferred port first."""
    if _is_port_available(preferred):
        return preferred

    # Scan upward from preferred
    for port in range(preferred + 1, range_end + 1):
        if _is_port_available(port):
            return port

    # Scan from range_start if nothing found above
    for port in range(range_start, preferred):
        if _is_port_available(port):
            return port

    raise RuntimeError(f"No available port found in range {range_start}-{range_end}")


# ──────────────────────────────────────────────
#  Process management helpers
# ──────────────────────────────────────────────

def _kill_pid(pid: int) -> bool:
    """Kill a process by PID. Returns True if it was running."""
    try:
        if sys.platform == "win32":
            # taskkill /T kills the entire process tree
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        return True
    except (ProcessLookupError, OSError, PermissionError):
        return False


def _is_pid_alive(pid: int) -> bool:
    """Check if a process is still running."""
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                capture_output=True, text=True,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, OSError, PermissionError):
        return False


def _save_state(state: dict):
    """Write PIDs and ports to file for later stop/status."""
    PID_FILE.write_text(json.dumps(state, indent=2))


def _load_state() -> dict:
    """Read state from file."""
    if not PID_FILE.exists():
        return {}
    try:
        return json.loads(PID_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _clear_state():
    """Remove state file."""
    if PID_FILE.exists():
        PID_FILE.unlink()


# ──────────────────────────────────────────────
#  Start
# ──────────────────────────────────────────────

_processes: list[tuple[str, subprocess.Popen]] = []


def _prefix_stream(name: str, stream):
    """Read lines from a process stream and print with colored prefix."""
    color = SERVICE_COLORS.get(name, "")
    prefix = f"{color}[{name}]{C_RESET} "
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            print(f"{prefix}{line}", end="", flush=True)
    except (ValueError, OSError):
        pass


def _launch(name: str, cmd: list[str], cwd: str, env=None):
    """Launch a subprocess with prefixed output streaming."""
    merged_env = {**os.environ, **(env or {})}

    kwargs = {}
    if sys.platform != "win32":
        kwargs["preexec_fn"] = os.setsid  # Create process group for clean kill

    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=merged_env,
        bufsize=1,
        **kwargs,
    )
    _processes.append((name, proc))

    thread = threading.Thread(
        target=_prefix_stream,
        args=(name, proc.stdout),
        daemon=True,
    )
    thread.start()

    color = SERVICE_COLORS.get(name, "")
    print(f"{color}[{name}]{C_RESET} Started (PID {proc.pid})")
    return proc


def _cleanup_all():
    """Terminate all running subprocesses, entire process trees."""
    for name, proc in reversed(_processes):
        if proc.poll() is None:
            color = SERVICE_COLORS.get(name, "")
            print(f"{color}[{name}]{C_RESET} Stopping...")
            _kill_pid(proc.pid)

    # Wait for them to actually exit
    deadline = time.time() + 5
    for _, proc in _processes:
        remaining = max(0, deadline - time.time())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            proc.kill()

    _clear_state()


def cmd_start():
    """Start all services."""
    # Check if already running
    existing = _load_state()
    pids = existing.get("pids", {})
    alive = {name: pid for name, pid in pids.items() if _is_pid_alive(pid)}
    if alive:
        print(f"{C_RED}Services already running:{C_RESET}")
        for name, pid in alive.items():
            print(f"  {name}: PID {pid}")
        print(f"\nRun {C_BOLD}python dev.py stop{C_RESET} first.")
        sys.exit(1)

    # Detect open ports
    ports: dict[str, int] = {}
    for service, preferred in DEFAULT_PORTS.items():
        ports[service] = _find_open_port(preferred)

    print(f"{C_BOLD}{'=' * 50}")
    print("  Woodshed AI — Development Server")
    print(f"{'=' * 50}{C_RESET}")
    print()

    new_pids: dict[str, int] = {}

    # 1. Transcription service (optional)
    service_dir = ROOT_DIR / "services" / "basic-pitch"
    venv_python = service_dir / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = service_dir / "venv" / "bin" / "python"
    app_script = service_dir / "app.py"

    if venv_python.exists() and app_script.exists():
        proc = _launch(
            "transcription",
            [str(venv_python), str(app_script), "--port", str(ports["transcription"])],
            str(service_dir),
            env={"PORT": str(ports["transcription"])},
        )
        new_pids["transcription"] = proc.pid
    else:
        print(f"{C_CYAN}[transcription]{C_RESET} Skipped (venv not found)")

    # 2. FastAPI backend
    venv_dir = ROOT_DIR / "venv"
    python_exe = venv_dir / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = venv_dir / "bin" / "python"
    if not python_exe.exists():
        python_exe = Path(sys.executable)

    backend_port = ports["backend"]
    frontend_port = ports["frontend"]

    proc = _launch(
        "backend",
        [str(python_exe), "-m", "uvicorn", "app.api.main:create_app",
         "--factory", "--host", "0.0.0.0", "--port", str(backend_port), "--reload"],
        str(ROOT_DIR),
        env={
            "API_PORT": str(backend_port),
            "FRONTEND_URL": f"http://localhost:{frontend_port}",
            "TRANSCRIPTION_SERVICE_URL": f"http://localhost:{ports['transcription']}",
        },
    )
    new_pids["backend"] = proc.pid

    # 3. Next.js frontend
    frontend_dir = ROOT_DIR / "frontend"
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    proc = _launch(
        "frontend",
        [npm_cmd, "run", "dev", "--", "--port", str(frontend_port)],
        str(frontend_dir),
        env={"NEXT_PUBLIC_API_URL": f"http://localhost:{backend_port}"},
    )
    new_pids["frontend"] = proc.pid

    # Save PIDs and ports for stop/status commands
    _save_state({"pids": new_pids, "ports": ports})

    print()
    print(f"  {C_GREEN}Backend:{C_RESET}  http://localhost:{backend_port}")
    print(f"  {C_GREEN}Frontend:{C_RESET} http://localhost:{frontend_port}")
    print(f"  {C_GREEN}API docs:{C_RESET} http://localhost:{backend_port}/docs")
    print()
    print(f"Press Ctrl+C to stop, or run {C_BOLD}python dev.py stop{C_RESET} from another terminal.")
    print()

    # Wait for exit
    try:
        while True:
            for name, proc in _processes:
                if proc.poll() is not None:
                    color = SERVICE_COLORS.get(name, "")
                    print(f"\n{color}[{name}]{C_RESET} exited (code {proc.returncode}). Shutting down...")
                    _cleanup_all()
                    return
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{C_BOLD}Shutting down all services...{C_RESET}")
        _cleanup_all()
        print(f"{C_GREEN}All services stopped.{C_RESET}")


# ──────────────────────────────────────────────
#  Stop
# ──────────────────────────────────────────────

def cmd_stop():
    """Stop all running services by PID."""
    state = _load_state()
    pids = state.get("pids", {})
    if not pids:
        print("No services recorded in .dev.pids")
        return

    stopped = 0
    for name, pid in pids.items():
        color = SERVICE_COLORS.get(name, "")
        if _is_pid_alive(pid):
            print(f"{color}[{name}]{C_RESET} Stopping PID {pid}...")
            _kill_pid(pid)
            stopped += 1
        else:
            print(f"{color}[{name}]{C_RESET} Already stopped (PID {pid})")

    _clear_state()

    if stopped:
        print(f"\n{C_GREEN}Stopped {stopped} service(s).{C_RESET}")
    else:
        print(f"\n{C_GREEN}No running services found.{C_RESET}")


# ──────────────────────────────────────────────
#  Status
# ──────────────────────────────────────────────

def cmd_status():
    """Show which services are running."""
    state = _load_state()
    pids = state.get("pids", {})
    ports = state.get("ports", {})
    if not pids:
        print("No services recorded. Start with: python dev.py")
        return

    print(f"{C_BOLD}Service Status:{C_RESET}")
    for name, pid in pids.items():
        color = SERVICE_COLORS.get(name, "")
        alive = _is_pid_alive(pid)
        dot = f"{C_GREEN}●{C_RESET}" if alive else f"{C_RED}●{C_RESET}"
        status = "running" if alive else "stopped"
        port_info = f" → :{ports[name]}" if name in ports else ""
        print(f"  {dot} {color}{name}{C_RESET} (PID {pid}{port_info}) — {status}")


# ──────────────────────────────────────────────
#  CLI entry point
# ──────────────────────────────────────────────

COMMANDS = {
    "start": cmd_start,
    "stop": cmd_stop,
    "status": cmd_status,
}

if __name__ == "__main__":
    # Handle Ctrl+C gracefully on Windows
    if sys.platform == "win32":
        try:
            signal.signal(signal.SIGBREAK, lambda *_: None)
        except (OSError, ValueError):
            pass

    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"

    if cmd in ("-h", "--help", "help"):
        print(f"Usage: python dev.py [start|stop|status]")
        print()
        print("  start    Start all services (default)")
        print("  stop     Stop all running services")
        print("  status   Show which services are running")
        sys.exit(0)

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Usage: python dev.py [start|stop|status]")
        sys.exit(1)

    COMMANDS[cmd]()
