import os
import json
import tempfile
import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from taskchecker.models import Task


def get_data_dir() -> Path:
    """Return the base directory for TaskChecker data (~/.taskchecker)."""
    # Allow override via environment variable if desired
    custom_dir = os.environ.get("TASKCHECKER_DATA_DIR")
    if custom_dir:
        base_dir = Path(custom_dir)
    else:
        base_dir = Path.home() / ".taskchecker"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_tasks_file_path() -> Path:
    return get_data_dir() / "tasks.json"


def get_config_file_path() -> Path:
    return get_data_dir() / "config.json"


def get_pid_file_path() -> Path:
    return get_data_dir() / "daemon.pid"


def get_log_file_path() -> Path:
    return get_data_dir() / "daemon.log"


class StorageManager:
    """Handles thread-safe, atomic persistence for tasks."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or get_tasks_file_path()

    def load_tasks(self) -> List[Task]:
        """Load all tasks from JSON storage."""
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Task.from_dict(item) for item in data]
        except (json.JSONDecodeError, OSError):
            # Backup corrupted file if possible
            backup = self.file_path.with_suffix(".corrupt.bak")
            try:
                if self.file_path.exists():
                    os.replace(self.file_path, backup)
            except OSError:
                pass
            return []

    def save_tasks(self, tasks: List[Task]) -> None:
        """Atomically save tasks to JSON file."""
        data = [t.to_dict() for t in tasks]
        dir_name = self.file_path.parent
        dir_name.mkdir(parents=True, exist_ok=True)

        # Atomic write via temp file in same directory
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            dir=str(dir_name),
            delete=False,
            encoding="utf-8"
        )
        try:
            json.dump(data, temp_file, indent=2, ensure_ascii=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            os.replace(temp_file.name, str(self.file_path))
        except Exception:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)
            raise

    def get_next_id(self, tasks: Optional[List[Task]] = None) -> int:
        if tasks is None:
            tasks = self.load_tasks()
        if not tasks:
            return 1
        return max(t.id for t in tasks) + 1

    def add_task(
        self,
        title: str,
        due_date: str,
        priority: str = "medium",
        notes: str = ""
    ) -> Task:
        tasks = self.load_tasks()
        new_id = self.get_next_id(tasks)
        task = Task(
            id=new_id,
            title=title,
            due_date=due_date,
            priority=priority,
            status="pending",
            notes=notes
        )
        tasks.append(task)
        self.save_tasks(tasks)
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        tasks = self.load_tasks()
        for t in tasks:
            if t.id == task_id:
                return t
        return None

    def update_task(self, updated_task: Task) -> bool:
        tasks = self.load_tasks()
        for i, t in enumerate(tasks):
            if t.id == updated_task.id:
                tasks[i] = updated_task
                self.save_tasks(tasks)
                return True
        return False

    def remove_task(self, task_id: int) -> Optional[Task]:
        tasks = self.load_tasks()
        found = None
        remaining = []
        for t in tasks:
            if t.id == task_id:
                found = t
            else:
                remaining.append(t)
        if found:
            self.save_tasks(remaining)
        return found

    def mark_completed(self, task_id: int) -> Optional[Task]:
        tasks = self.load_tasks()
        target = None
        for t in tasks:
            if t.id == task_id:
                t.status = "completed"
                t.completed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                target = t
                break
        if target:
            self.save_tasks(tasks)
        return target

    def mark_pending(self, task_id: int) -> Optional[Task]:
        tasks = self.load_tasks()
        target = None
        for t in tasks:
            if t.id == task_id:
                t.status = "pending"
                t.completed_at = None
                target = t
                break
        if target:
            self.save_tasks(tasks)
        return target

    def clear_completed(self) -> int:
        tasks = self.load_tasks()
        remaining = [t for t in tasks if t.status != "completed"]
        cleared_count = len(tasks) - len(remaining)
        if cleared_count > 0:
            self.save_tasks(remaining)
        return cleared_count
