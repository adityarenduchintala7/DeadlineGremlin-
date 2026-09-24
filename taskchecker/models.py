import datetime
from typing import Optional, List, Dict, Any, Tuple


class Task:
    """Represents a single task with deadline, priority, status, and reminder tracking."""

    PRIORITIES = ["low", "medium", "high", "urgent"]

    def __init__(
        self,
        id: int,
        title: str,
        due_date: str,
        priority: str = "medium",
        status: str = "pending",
        notes: str = "",
        created_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        notified_milestones: Optional[List[str]] = None,
        last_notified_at: Optional[str] = None,
    ):
        self.id = id
        self.title = title.strip()
        self.due_date = due_date
        self.priority = priority.lower() if priority.lower() in self.PRIORITIES else "medium"
        self.status = status
        self.notes = notes.strip()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created_at = created_at or now_str
        self.completed_at = completed_at
        self.notified_milestones = notified_milestones or []
        self.last_notified_at = last_notified_at

    @property
    def due_datetime(self) -> datetime.datetime:
        """Parse due_date string into datetime object."""
        try:
            return datetime.datetime.strptime(self.due_date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.datetime.strptime(self.due_date, "%Y-%m-%d %H:%M")
            except ValueError:
                return datetime.datetime.fromisoformat(self.due_date)

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_overdue(self) -> bool:
        if self.is_completed:
            return False
        return datetime.datetime.now() > self.due_datetime

    def time_remaining(self) -> Tuple[datetime.timedelta, bool, str]:
        """
        Calculate time remaining until due date.
        Returns (timedelta, is_overdue, human_readable_string).
        """
        now = datetime.datetime.now()
        due = self.due_datetime
        diff = due - now

        if diff.total_seconds() < 0:
            is_overdue = True
            abs_diff = now - due
            total_seconds = int(abs_diff.total_seconds())
        else:
            is_overdue = False
            total_seconds = int(diff.total_seconds())

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")

        time_str = " ".join(parts)
        if is_overdue:
            human_str = f"OVERDUE by {time_str}"
        else:
            human_str = f"in {time_str}"

        return diff, is_overdue, human_str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "notified_milestones": self.notified_milestones,
            "last_notified_at": self.last_notified_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        return cls(
            id=data["id"],
            title=data["title"],
            due_date=data["due_date"],
            priority=data.get("priority", "medium"),
            status=data.get("status", "pending"),
            notes=data.get("notes", ""),
            created_at=data.get("created_at"),
            completed_at=data.get("completed_at"),
            notified_milestones=data.get("notified_milestones", []),
            last_notified_at=data.get("last_notified_at"),
        )
