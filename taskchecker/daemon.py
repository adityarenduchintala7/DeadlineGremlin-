import os
import sys
import time
import signal
import datetime
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple

from taskchecker.models import Task
from taskchecker.storage import (
    StorageManager,
    get_pid_file_path,
    get_log_file_path,
    get_data_dir
)
from taskchecker.notifier import notify_task

# Set up logging
log_file = get_log_file_path()
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("taskchecker.daemon")

# Define milestone thresholds in seconds
# Order is from longest time to shortest
MILESTONES = [
    ("48h", 48 * 3600),
    ("24h", 24 * 3600),
    ("12h", 12 * 3600),
    ("6h",  6 * 3600),
    ("3h",  3 * 3600),
    ("2h",  2 * 3600),
    ("1h",  1 * 3600),
    ("30m", 30 * 60),
    ("15m", 15 * 60),
    ("5m",  5 * 60),
]


def is_pid_running(pid: int) -> bool:
    """Check if a process with given PID is currently active."""
    if pid <= 0:
        return False
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        # Fallback to os.kill(0) on platforms that support it
        try:
            os.kill(pid, 0)
            return True
        except (OSError, PermissionError):
            return False


def get_running_daemon_pid() -> Optional[int]:
    """Returns the PID of running daemon, or None if not running."""
    pid_file = get_pid_file_path()
    if not pid_file.exists():
        return None
    try:
        pid = int(pid_file.read_text().strip())
        if is_pid_running(pid):
            return pid
        else:
            # Stale PID file
            try:
                pid_file.unlink()
            except OSError:
                pass
            return None
    except Exception:
        return None


def write_pid(pid: int) -> None:
    pid_file = get_pid_file_path()
    pid_file.write_text(str(pid))


def remove_pid() -> None:
    pid_file = get_pid_file_path()
    if pid_file.exists():
        try:
            pid_file.unlink()
        except OSError:
            pass


def evaluate_task_notifications(task: Task, now: datetime.datetime) -> Optional[Tuple[str, str]]:
    """
    Evaluates whether a task needs a notification right now.
    Returns (milestone_code, urgency_type) if notification should fire, else None.
    Updates task.notified_milestones in-place to prevent repeated toasts.
    """
    if task.is_completed:
        return None

    due = task.due_datetime
    diff_sec = (due - now).total_seconds()
    last_notified = None
    if task.last_notified_at:
        try:
            last_notified = datetime.datetime.fromisoformat(task.last_notified_at)
        except ValueError:
            pass

    # 1. Overdue checks
    if diff_sec <= 0:
        # If due milestone hasn't been fired yet
        if "due" not in task.notified_milestones:
            # Mark all approaching milestones as passed
            for code, _ in MILESTONES:
                if code not in task.notified_milestones:
                    task.notified_milestones.append(code)
            task.notified_milestones.append("due")
            return ("due", "due")

        # Overdue periodic reminders (every 1 to 2 hours while overdue)
        overdue_sec = abs(diff_sec)
        overdue_hours = int(overdue_sec // 3600)
        overdue_tag = f"overdue_{overdue_hours}h"

        if overdue_hours >= 1 and overdue_tag not in task.notified_milestones:
            # Ensure at least 45 minutes passed since last notification
            if not last_notified or (now - last_notified).total_seconds() >= 2700:
                task.notified_milestones.append(overdue_tag)
                return (overdue_tag, "overdue")

        return None

    # 2. Approaching deadlines (diff_sec > 0)
    # Find the smallest milestone threshold that diff_sec is <= to
    current_milestone = None
    for code, threshold_sec in reversed(MILESTONES):
        if diff_sec <= threshold_sec:
            current_milestone = code
            break

    if not current_milestone:
        return None

    # Check if this milestone has already been notified
    if current_milestone in task.notified_milestones:
        return None

    # Mark this and any larger milestones that might have been skipped while machine was asleep/offline
    # e.g., if we jump from 12h straight to 2h, mark 12h, 6h, 3h as notified so we don't retroactively fire them
    mark = False
    for code, _ in MILESTONES:
        if code == current_milestone:
            mark = True
        if not mark and code not in task.notified_milestones:
            task.notified_milestones.append(code)

    task.notified_milestones.append(current_milestone)
    return (current_milestone, current_milestone)


def check_and_notify_all(storage: StorageManager) -> int:
    """
    Checks all pending tasks and sends any due notifications.
    Returns count of notifications sent.
    """
    tasks = storage.load_tasks()
    now = datetime.datetime.now()
    notifications_sent = 0
    updated = False

    for task in tasks:
        if task.is_completed:
            continue

        result = evaluate_task_notifications(task, now)
        if result:
            milestone, urgency = result
            logger.info(f"Triggering notification for Task #{task.id} '{task.title}' [Milestone: {milestone}]")
            success = notify_task(task, urgency)
            if success:
                task.last_notified_at = now.isoformat()
                notifications_sent += 1
                updated = True
            else:
                logger.warning(f"Failed to deliver notification for Task #{task.id}")

    if updated:
        storage.save_tasks(tasks)

    return notifications_sent


class TaskCheckerDaemon:
    """Daemon process loop that monitors tasks and sends notifications."""

    def __init__(self, check_interval_sec: int = 30):
        self.check_interval_sec = check_interval_sec
        self.storage = StorageManager()
        self.running = False

    def handle_signal(self, signum, frame):
        logger.info(f"Daemon received signal {signum}, stopping...")
        self.running = False

    def run(self):
        """Main daemon loop."""
        existing_pid = get_running_daemon_pid()
        if existing_pid and existing_pid != os.getpid():
            logger.warning(f"Daemon is already running with PID {existing_pid}. Exiting.")
            sys.exit(0)

        write_pid(os.getpid())
        self.running = True
        logger.info(f"TaskChecker Daemon started (PID {os.getpid()}, interval {self.check_interval_sec}s)")

        # Register signals
        try:
            signal.signal(signal.SIGTERM, self.handle_signal)
            signal.signal(signal.SIGINT, self.handle_signal)
        except Exception:
            pass

        try:
            while self.running:
                try:
                    check_and_notify_all(self.storage)
                except Exception as e:
                    logger.error(f"Error checking tasks: {e}", exc_info=True)

                # Sleep in short increments to respond quickly to termination
                for _ in range(self.check_interval_sec):
                    if not self.running:
                        break
                    time.sleep(1)
        finally:
            remove_pid()
            logger.info("TaskChecker Daemon stopped.")


def start_daemon_background() -> Tuple[bool, str]:
    """Starts the daemon as a detached background process."""
    current_pid = get_running_daemon_pid()
    if current_pid:
        return False, f"Daemon is already running (PID {current_pid})"

    # Find pythonw.exe or python.exe
    python_exe = sys.executable
    if python_exe.endswith("python.exe"):
        pythonw = python_exe[:-10] + "pythonw.exe"
        if os.path.exists(pythonw):
            python_exe = pythonw

    main_script = str(Path(__file__).parent / "main.py")

    cmd = [python_exe, main_script, "daemon", "run"]

    creationflags = 0
    if sys.platform == "win32":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        creationflags = 0x00000008 | 0x00000200

    try:
        proc = subprocess.Popen(
            cmd,
            creationflags=creationflags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        # Give it a moment to write PID
        time.sleep(1.0)
        active_pid = get_running_daemon_pid()
        if active_pid:
            return True, f"Daemon started successfully in background (PID {active_pid})"
        elif proc.poll() is None:
            return True, f"Daemon started in background (PID {proc.pid})"
        else:
            return False, f"Daemon failed to start (Process exited immediately with code {proc.returncode})"
    except Exception as e:
        return False, f"Failed to start daemon: {e}"


def stop_daemon() -> Tuple[bool, str]:
    """Stops the running daemon process."""
    pid = get_running_daemon_pid()
    if not pid:
        remove_pid()
        return False, "Daemon is not currently running"

    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        # PROCESS_TERMINATE = 0x0001
        handle = kernel32.OpenProcess(0x0001, False, pid)
        if handle:
            kernel32.TerminateProcess(handle, 0)
            kernel32.CloseHandle(handle)
        else:
            os.kill(pid, signal.SIGTERM)

        time.sleep(0.5)
        remove_pid()
        return True, f"Daemon (PID {pid}) stopped successfully"
    except Exception as e:
        # Fallback using taskkill on Windows
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True)
            remove_pid()
            return True, f"Daemon (PID {pid}) stopped"
        except Exception:
            return False, f"Could not stop daemon PID {pid}: {e}"
