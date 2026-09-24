import os
import sys
import argparse
import datetime
from pathlib import Path
from typing import List, Optional

from taskchecker import __version__
from taskchecker.models import Task
from taskchecker.date_parser import parse_due_date, DateParseError
from taskchecker.storage import StorageManager, get_tasks_file_path, get_data_dir
from taskchecker.notifier import send_windows_toast
from taskchecker.daemon import (
    start_daemon_background,
    stop_daemon,
    get_running_daemon_pid,
    check_and_notify_all,
    TaskCheckerDaemon
)
from taskchecker.autostart import (
    enable_autostart,
    disable_autostart,
    is_autostart_enabled
)


# Terminal ANSI Colors (supported in modern Windows Terminal, CMD, PowerShell)
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"


def supports_color() -> bool:
    """Check if the current terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR"):
        return False
    if sys.stdout is None or not hasattr(sys.stdout, "isatty"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


USE_COLOR = supports_color()


def c(text: str, color_code: str) -> str:
    """Colorize text if terminal supports color."""
    if not USE_COLOR:
        return text
    return f"{color_code}{text}{Colors.RESET}"


def priority_badge(priority: str) -> str:
    p = priority.lower()
    if p in ("urgent", "high"):
        return c(f"[{p.upper()}]", Colors.RED + Colors.BOLD)
    elif p == "medium":
        return c(f"[{p.upper()}]", Colors.YELLOW)
    else:
        return c(f"[{p.upper()}]", Colors.CYAN)


def format_time_remaining(task: Task) -> str:
    if task.is_completed:
        return c("✓ Completed", Colors.GREEN)

    diff, is_overdue, human_str = task.time_remaining()
    total_sec = diff.total_seconds()

    if is_overdue:
        return c(f"🚨 {human_str}", Colors.RED + Colors.BOLD)
    elif total_sec <= 3600:  # < 1 hour
        return c(f"⏳ {human_str}", Colors.RED)
    elif total_sec <= 24 * 3600:  # < 24 hours
        return c(f"⏰ {human_str}", Colors.YELLOW)
    else:
        return c(f"📅 {human_str}", Colors.GREEN)


class CLI:
    def __init__(self):
        self.storage = StorageManager()

    def cmd_add(self, args):
        title = args.title
        deadline_raw = args.due

        if not title:
            print(c("Error: Task title cannot be empty.", Colors.RED))
            return 1

        if not deadline_raw:
            print(c("Error: Deadline is required. Use e.g. 'in 2 hours', 'today 6pm', 'tomorrow 9am'.", Colors.RED))
            return 1

        try:
            parsed_due = parse_due_date(deadline_raw)
        except DateParseError as e:
            print(c(f"Error: {e}", Colors.RED))
            return 1

        priority = args.priority.lower() if args.priority else "medium"
        notes = args.notes or ""

        task = self.storage.add_task(
            title=title,
            due_date=parsed_due,
            priority=priority,
            notes=notes
        )

        _, is_overdue, human_left = task.time_remaining()
        due_fmt = task.due_datetime.strftime("%Y-%m-%d %I:%M %p")

        print(c("✓ Task added successfully!", Colors.GREEN + Colors.BOLD))
        print(f"  {c(f'#{task.id}', Colors.BOLD)} {task.title} {priority_badge(task.priority)}")
        print(f"  Deadline: {c(due_fmt, Colors.CYAN)} ({format_time_remaining(task)})")
        if task.notes:
            print(f"  Notes: {task.notes}")

        # Check daemon status and prompt user if not running
        daemon_pid = get_running_daemon_pid()
        if not daemon_pid:
            print()
            print(c("💡 Background reminder service is currently offline.", Colors.YELLOW))
            print(f"   Start it now with: {c('task daemon start', Colors.BOLD)}")
            print(f"   Or enable autostart on PC reboot: {c('task autostart enable', Colors.BOLD)}")
        return 0

    def cmd_list(self, args):
        tasks = self.storage.load_tasks()

        if not tasks:
            print(c("No tasks found! Add one with: ", Colors.YELLOW) + c('task add "My Task" "tomorrow 5pm"', Colors.BOLD))
            return 0

        # Filter
        show_all = getattr(args, "all", False)
        show_completed_only = getattr(args, "completed", False)

        if show_completed_only:
            filtered = [t for t in tasks if t.is_completed]
        elif not show_all:
            filtered = [t for t in tasks if not t.is_completed]
        else:
            filtered = tasks

        if not filtered:
            if show_completed_only:
                print(c("No completed tasks.", Colors.DIM))
            else:
                print(c("🎉 No pending tasks! All caught up.", Colors.GREEN + Colors.BOLD))
                print(f"View completed tasks with: {c('task list --all', Colors.CYAN)}")
            return 0

        # Sort tasks by due date
        filtered.sort(key=lambda t: t.due_datetime)

        print()
        header = f"{'ID':<4} {'PRIORITY':<9} {'DEADLINE':<18} {'TIME LEFT / STATUS':<24} {'TITLE'}"
        print(c(header, Colors.BOLD + Colors.UNDERLINE))

        pending_count = 0
        overdue_count = 0
        completed_count = 0

        for t in filtered:
            if t.is_completed:
                completed_count += 1
                status_str = c("✓ Done", Colors.GREEN)
                title_str = c(t.title, Colors.DIM)
                due_str = c(t.due_datetime.strftime("%b %d %I:%M%p"), Colors.DIM)
                prio_str = c("[DONE]", Colors.DIM)
            else:
                pending_count += 1
                diff, is_overdue, _ = t.time_remaining()
                if is_overdue:
                    overdue_count += 1
                status_str = format_time_remaining(t)
                due_str = t.due_datetime.strftime("%b %d %I:%M%p")
                prio_str = priority_badge(t.priority)
                title_str = c(t.title, Colors.BOLD)

            id_str = f"#{t.id:<3}"
            print(f"{id_str} {prio_str:<9} {due_str:<18} {status_str:<24} {title_str}")
            if t.notes and not t.is_completed:
                print(f"     {c('└─ Notes: ' + t.notes, Colors.DIM)}")

        print()
        summary_parts = []
        if pending_count:
            summary_parts.append(f"{c(str(pending_count), Colors.BOLD)} pending")
        if overdue_count:
            summary_parts.append(f"{c(str(overdue_count) + ' OVERDUE', Colors.RED + Colors.BOLD)}")
        if completed_count:
            summary_parts.append(f"{c(str(completed_count), Colors.GREEN)} completed")

        daemon_pid = get_running_daemon_pid()
        daemon_badge = c("● Active", Colors.GREEN) if daemon_pid else c("○ Stopped", Colors.RED)
        print(f"Summary: {', '.join(summary_parts)}  |  Notifier: {daemon_badge}")
        print()
        return 0

    def cmd_remove(self, args):
        for task_id in args.ids:
            removed = self.storage.remove_task(task_id)
            if removed:
                print(c(f"✓ Removed task #{task_id}: '{removed.title}'", Colors.GREEN))
            else:
                print(c(f"Error: Task #{task_id} not found.", Colors.RED))
        return 0

    def cmd_done(self, args):
        for task_id in args.ids:
            task = self.storage.mark_completed(task_id)
            if task:
                print(c(f"🎉 Marked task #{task_id} as COMPLETED: '{task.title}'!", Colors.GREEN + Colors.BOLD))
                print(c("   Notifications for this task are now stopped.", Colors.DIM))
            else:
                print(c(f"Error: Task #{task_id} not found.", Colors.RED))
        return 0

    def cmd_undo(self, args):
        for task_id in args.ids:
            task = self.storage.mark_pending(task_id)
            if task:
                print(c(f"✓ Reopened task #{task_id}: '{task.title}' (status: pending)", Colors.CYAN))
            else:
                print(c(f"Error: Task #{task_id} not found.", Colors.RED))
        return 0

    def cmd_clear(self, args):
        count = self.storage.clear_completed()
        if count > 0:
            print(c(f"✓ Cleared {count} completed task(s).", Colors.GREEN))
        else:
            print(c("No completed tasks to clear.", Colors.YELLOW))
        return 0

    def cmd_edit(self, args):
        task = self.storage.get_task(args.id)
        if not task:
            print(c(f"Error: Task #{args.id} not found.", Colors.RED))
            return 1

        if args.title:
            task.title = args.title.strip()
        if args.due:
            try:
                task.due_date = parse_due_date(args.due)
                # Reset milestone notifications when deadline changes
                task.notified_milestones = []
            except DateParseError as e:
                print(c(f"Error: {e}", Colors.RED))
                return 1
        if args.priority:
            task.priority = args.priority.lower()
        if args.notes is not None:
            task.notes = args.notes.strip()

        self.storage.update_task(task)
        print(c(f"✓ Task #{task.id} updated successfully!", Colors.GREEN))
        print(f"  Title:    {task.title}")
        print(f"  Deadline: {task.due_datetime.strftime('%Y-%m-%d %I:%M %p')}")
        print(f"  Priority: {task.priority.upper()}")
        return 0

    def cmd_notify(self, args):
        print("Checking tasks for notifications...")
        count = check_and_notify_all(self.storage)
        if count > 0:
            print(c(f"✓ Delivered {count} notification(s).", Colors.GREEN))
        else:
            print(c("No tasks currently require notification.", Colors.CYAN))
        return 0

    def cmd_test_notify(self, args):
        print("Sending test notification to Windows...")
        now_str = datetime.datetime.now().strftime("%I:%M:%S %p")
        success = send_windows_toast(
            title="🔔 TaskChecker Test Alert",
            message=f"Windows Toast notifications are working perfectly! Time: {now_str}"
        )
        if success:
            print(c("✓ Test notification sent! Check the bottom-right corner of your screen.", Colors.GREEN + Colors.BOLD))
        else:
            print(c("Failed to send toast notification. Check Windows Notification settings.", Colors.RED))
        return 0

    def cmd_daemon(self, args):
        action = args.action

        if action == "start":
            success, msg = start_daemon_background()
            if success:
                print(c(f"✓ {msg}", Colors.GREEN + Colors.BOLD))
            else:
                print(c(f"Notice: {msg}", Colors.YELLOW))

        elif action == "stop":
            success, msg = stop_daemon()
            if success:
                print(c(f"✓ {msg}", Colors.GREEN))
            else:
                print(c(f"Notice: {msg}", Colors.YELLOW))

        elif action == "restart":
            stop_daemon()
            success, msg = start_daemon_background()
            print(c(f"✓ Daemon restarted. {msg}", Colors.GREEN))

        elif action == "status":
            pid = get_running_daemon_pid()
            auto = is_autostart_enabled()
            print(c("TaskChecker Daemon Status:", Colors.BOLD))
            if pid:
                print(f"  Process:   {c(f'RUNNING (PID {pid})', Colors.GREEN + Colors.BOLD)}")
            else:
                print(f"  Process:   {c('STOPPED', Colors.RED)}")
            print(f"  Autostart: {c('ENABLED (Starts on PC boot)', Colors.GREEN) if auto else c('DISABLED', Colors.YELLOW)}")
            print(f"  Data Path: {get_tasks_file_path()}")

        elif action == "run":
            daemon = TaskCheckerDaemon()
            daemon.run()

        return 0

    def cmd_autostart(self, args):
        action = args.action
        if action == "enable":
            success, msg = enable_autostart()
            if success:
                print(c(f"✓ {msg}", Colors.GREEN + Colors.BOLD))
                # Also start the daemon right now if not already running
                if not get_running_daemon_pid():
                    start_daemon_background()
                    print(c("✓ Background notifier daemon also started now.", Colors.GREEN))
            else:
                print(c(f"Error: {msg}", Colors.RED))
        elif action == "disable":
            success, msg = disable_autostart()
            print(c(f"✓ {msg}", Colors.GREEN))
        elif action == "status":
            enabled = is_autostart_enabled()
            if enabled:
                print(c("✓ Autostart is ENABLED. TaskChecker notifications will persist across PC reboots.", Colors.GREEN + Colors.BOLD))
            else:
                print(c("Autostart is DISABLED. Enable it with: task autostart enable", Colors.YELLOW))
        return 0

    def cmd_path(self, args):
        """Adds current project directory to User PATH environment variable."""
        current_dir = str(Path(__file__).parent.parent.resolve())
        print(f"Adding '{current_dir}' to your Windows User PATH...")

        import subprocess
        ps_cmd = f"""
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        $target = "{current_dir}"
        if ($currentPath -split ';' -notcontains $target) {{
            $newPath = "$currentPath;$target"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            Write-Host "SUCCESS"
        }} else {{
            Write-Host "ALREADY_IN_PATH"
        }}
        """
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        out = res.stdout.strip()
        if "SUCCESS" in out:
            print(c("✓ Successfully added TaskChecker to your User PATH!", Colors.GREEN + Colors.BOLD))
            print("  You can now open a new Command Prompt or PowerShell window anywhere and simply type:")
            print(f"  {c('task list', Colors.CYAN)} or {c('task add \"My task\" \"in 2 hours\"', Colors.CYAN)}")
        elif "ALREADY_IN_PATH" in out:
            print(c("✓ TaskChecker is already in your User PATH!", Colors.GREEN))
        else:
            print(c(f"Notice: {res.stderr or res.stdout}", Colors.YELLOW))
        return 0

    def cmd_cheatsheet(self, args):
        sheet_path = Path(__file__).parent.parent / "CHEATSHEET.md"
        if sheet_path.exists():
            print(sheet_path.read_text(encoding="utf-8"))
        else:
            print(c("CHEATSHEET.md not found.", Colors.RED))
        return 0



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="task",
        description="TaskChecker: Terminal-based task deadline monitor with desktop notifications.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  task add "Finish project presentation" "tomorrow 5pm" --priority high
  task add "Take medicines" "in 30 mins"
  task add "Submit tax forms" "2026-09-30 18:00"
  task list
  task list --all
  task done 1
  task remove 2
  task daemon start
  task autostart enable
  task test-notify
"""
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # ADD
    p_add = subparsers.add_parser("add", help="Add a new task with a deadline")
    p_add.add_argument("title", help="Task description / title")
    p_add.add_argument("due", nargs="?", default=None, help="Deadline: 'in 2 hours', 'today 6pm', 'tomorrow 9am', '2026-09-25 15:00'")
    p_add.add_argument("-d", "--due-date", dest="due_flag", help="Alternative flag for deadline")
    p_add.add_argument("-p", "--priority", choices=["low", "medium", "high", "urgent"], default="medium", help="Priority level (default: medium)")
    p_add.add_argument("-n", "--notes", default="", help="Optional notes or details")

    # LIST
    p_list = subparsers.add_parser("list", aliases=["ls"], help="List tasks")
    p_list.add_argument("-a", "--all", action="store_true", help="Include completed tasks")
    p_list.add_argument("-c", "--completed", action="store_true", help="Show only completed tasks")

    # DONE / COMPLETE
    p_done = subparsers.add_parser("done", aliases=["complete"], help="Mark task(s) as completed")
    p_done.add_argument("ids", type=int, nargs="+", help="One or more task IDs to mark complete")

    # UNDO
    p_undo = subparsers.add_parser("undo", help="Reopen a completed task")
    p_undo.add_argument("ids", type=int, nargs="+", help="One or more task IDs to reopen")

    # REMOVE / DELETE
    p_rm = subparsers.add_parser("remove", aliases=["rm", "delete"], help="Permanently delete task(s)")
    p_rm.add_argument("ids", type=int, nargs="+", help="One or more task IDs to delete")

    # CLEAR
    p_clear = subparsers.add_parser("clear", help="Clear all completed tasks")

    # EDIT
    p_edit = subparsers.add_parser("edit", help="Edit an existing task")
    p_edit.add_argument("id", type=int, help="Task ID to edit")
    p_edit.add_argument("-t", "--title", help="New title")
    p_edit.add_argument("-d", "--due", help="New deadline")
    p_edit.add_argument("-p", "--priority", choices=["low", "medium", "high", "urgent"], help="New priority")
    p_edit.add_argument("-n", "--notes", help="New notes")

    # NOTIFY
    p_notify = subparsers.add_parser("notify", help="Manually check tasks and send due notifications now")

    # TEST-NOTIFY
    p_test = subparsers.add_parser("test-notify", help="Send a test notification to verify Windows toasts")

    # DAEMON
    p_daemon = subparsers.add_parser("daemon", help="Manage background notification service")
    p_daemon.add_argument("action", choices=["start", "stop", "restart", "status", "run"], help="Daemon action")

    # AUTOSTART
    p_auto = subparsers.add_parser("autostart", help="Configure automatic startup when Windows reboots")
    p_auto.add_argument("action", choices=["enable", "disable", "status"], help="Autostart action")

    # PATH INSTALL
    p_path = subparsers.add_parser("install-path", aliases=["path"], help="Add TaskChecker to Windows User PATH")

    # CHEATSHEET
    p_cheat = subparsers.add_parser("cheatsheet", help="Display full command cheatsheet and examples")

    return parser


def main():
    parser = build_parser()

    # Pre-process arguments to support aliases and defaults
    args_list = sys.argv[1:]
    if not args_list:
        # Default behavior when running 'task' with no args: list tasks!
        args_list = ["list"]

    # Support shorthand 'task rm' or 'task ls'
    if args_list[0] in ("ls",):
        args_list[0] = "list"
    elif args_list[0] in ("rm", "delete"):
        args_list[0] = "remove"
    elif args_list[0] in ("complete",):
        args_list[0] = "done"

    args = parser.parse_args(args_list)
    cli = CLI()

    # Handle 'add' due flag fallback
    if args.subcommand == "add":
        if not args.due and getattr(args, "due_flag", None):
            args.due = args.due_flag

    handler_map = {
        "add": cli.cmd_add,
        "list": cli.cmd_list,
        "remove": cli.cmd_remove,
        "done": cli.cmd_done,
        "undo": cli.cmd_undo,
        "clear": cli.cmd_clear,
        "edit": cli.cmd_edit,
        "notify": cli.cmd_notify,
        "test-notify": cli.cmd_test_notify,
        "daemon": cli.cmd_daemon,
        "autostart": cli.cmd_autostart,
        "install-path": cli.cmd_path,
        "cheatsheet": cli.cmd_cheatsheet,
    }

    handler = handler_map.get(args.subcommand)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(0)
