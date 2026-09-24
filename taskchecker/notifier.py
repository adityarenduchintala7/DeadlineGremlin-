import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("taskchecker.notifier")

SCRIPT_DIR = Path(__file__).parent.resolve()
TOAST_PS1_PATH = SCRIPT_DIR / "toast.ps1"


def play_sound():
    """Plays Windows system alert sound."""
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass


def send_windows_toast(title: str, message: str, app_id: str = "TaskChecker") -> bool:
    """
    Sends a native Windows Toast notification using PowerShell and toast.ps1.
    Returns True if successfully sent, False otherwise.
    """
    if not TOAST_PS1_PATH.exists():
        logger.error(f"toast.ps1 not found at {TOAST_PS1_PATH}")
        return False

    try:
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(TOAST_PS1_PATH),
            "-Title", title,
            "-Message", message,
            "-AppId", app_id
        ]

        # Hide window on Windows
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        if result.returncode == 0:
            play_sound()
            return True
        else:
            err = result.stderr.strip() if result.stderr else result.stdout.strip()
            logger.warning(f"PowerShell toast error (code {result.returncode}): {err}")
            return False
    except Exception as e:
        logger.error(f"Failed to display toast notification: {e}")
        return False


def notify_task(task, urgency: str, extra_msg: Optional[str] = None) -> bool:
    """
    Convenience method to format and trigger a toast notification for a task.
    """
    due_display = task.due_datetime.strftime("%I:%M %p, %b %d")
    _, is_overdue, human_left = task.time_remaining()

    if urgency == "due":
        title = f"🚨 DUE NOW: {task.title}"
        body = f"Deadline reached! ({due_display})\nMark complete: task done {task.id}"
    elif urgency == "overdue":
        title = f"⚠️ OVERDUE: {task.title}"
        body = f"{human_left.capitalize()}!\nDeadline was {due_display}"
    elif urgency in ("5m", "15m", "30m"):
        title = f"⏳ Approaching Deadline: {task.title}"
        body = f"Due {human_left}! (Deadline: {due_display})"
    elif urgency in ("1h", "2h", "3h"):
        title = f"⏰ Task Reminder: {task.title}"
        body = f"Due {human_left}. (Deadline: {due_display})"
    elif urgency in ("6h", "12h", "24h"):
        title = f"📅 Upcoming Task: {task.title}"
        body = f"Due {human_left} at {due_display}"
    else:
        title = f"📌 Task Reminder: {task.title}"
        body = extra_msg or f"Due {human_left} (Deadline: {due_display})"

    if task.notes:
        body += f"\nNotes: {task.notes}"

    return send_windows_toast(title, body)
