import unittest
import os
import shutil
import tempfile
import datetime
from pathlib import Path

from taskchecker.models import Task
from taskchecker.date_parser import parse_due_date, parse_time_str, DateParseError
from taskchecker.storage import StorageManager
from taskchecker.daemon import evaluate_task_notifications, MILESTONES


class TestModels(unittest.TestCase):
    def test_task_creation_and_dict(self):
        task = Task(
            id=1,
            title="Complete project",
            due_date="2026-10-01 15:00:00",
            priority="high",
            notes="Important meeting"
        )
        self.assertEqual(task.id, 1)
        self.assertEqual(task.title, "Complete project")
        self.assertEqual(task.priority, "high")
        self.assertFalse(task.is_completed)

        d = task.to_dict()
        restored = Task.from_dict(d)
        self.assertEqual(restored.id, task.id)
        self.assertEqual(restored.title, task.title)
        self.assertEqual(restored.due_date, task.due_date)
        self.assertEqual(restored.priority, task.priority)

    def test_time_remaining_future(self):
        future_dt = (datetime.datetime.now() + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        task = Task(id=2, title="Future task", due_date=future_dt)
        diff, is_overdue, human_str = task.time_remaining()
        self.assertFalse(is_overdue)
        self.assertTrue(human_str.startswith("in 5h"))

    def test_time_remaining_overdue(self):
        past_dt = (datetime.datetime.now() - datetime.timedelta(hours=2, minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        task = Task(id=3, title="Past task", due_date=past_dt)
        diff, is_overdue, human_str = task.time_remaining()
        self.assertTrue(is_overdue)
        self.assertTrue(human_str.startswith("OVERDUE by 2h"))


class TestDateParser(unittest.TestCase):
    def test_relative_time(self):
        now = datetime.datetime.now()
        
        # 30 minutes
        due = parse_due_date("in 30 mins")
        dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
        self.assertTrue(29 <= (dt - now).total_seconds() / 60 <= 31)

        # 2 hours
        due = parse_due_date("in 2 hours")
        dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
        self.assertTrue(119 <= (dt - now).total_seconds() / 60 <= 121)

        # Combined
        due = parse_due_date("in 1h 30m")
        dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
        self.assertTrue(89 <= (dt - now).total_seconds() / 60 <= 91)

    def test_keywords(self):
        due = parse_due_date("today 6pm")
        dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
        self.assertEqual(dt.hour, 18)
        self.assertEqual(dt.minute, 0)

        due = parse_due_date("tomorrow 10am")
        dt = datetime.datetime.strptime(due, "%Y-%m-%d %H:%M:%S")
        self.assertEqual(dt.hour, 10)
        self.assertEqual(dt.minute, 0)

    def test_standard_formats(self):
        due = parse_due_date("2026-12-25 14:30")
        self.assertEqual(due, "2026-12-25 14:30:00")

    def test_invalid_date(self):
        with self.assertRaises(DateParseError):
            parse_due_date("invalid gibberish date string")


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tasks_file = Path(self.temp_dir) / "tasks.json"
        self.storage = StorageManager(self.tasks_file)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_crud_operations(self):
        # Empty
        tasks = self.storage.load_tasks()
        self.assertEqual(len(tasks), 0)

        # Add
        t1 = self.storage.add_task("Test task 1", "2026-10-01 12:00:00", priority="high")
        self.assertEqual(t1.id, 1)
        self.assertEqual(t1.title, "Test task 1")

        t2 = self.storage.add_task("Test task 2", "2026-10-02 12:00:00", priority="low")
        self.assertEqual(t2.id, 2)

        # Get
        fetched = self.storage.get_task(1)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Test task 1")

        # Complete
        completed = self.storage.mark_completed(1)
        self.assertEqual(completed.status, "completed")
        self.assertIsNotNone(completed.completed_at)

        # Clear completed
        cleared = self.storage.clear_completed()
        self.assertEqual(cleared, 1)
        remaining = self.storage.load_tasks()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].id, 2)

        # Remove
        removed = self.storage.remove_task(2)
        self.assertIsNotNone(removed)
        self.assertEqual(len(self.storage.load_tasks()), 0)


class TestNotificationEvaluation(unittest.TestCase):
    def test_milestone_trigger(self):
        now = datetime.datetime.now()
        
        # Task due in 25 minutes -> should hit "30m" milestone (diff <= 30m)
        due_25m = (now + datetime.timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S")
        task = Task(id=10, title="Check email", due_date=due_25m)

        res = evaluate_task_notifications(task, now)
        self.assertIsNotNone(res)
        milestone, urgency = res
        self.assertEqual(milestone, "30m")
        self.assertIn("30m", task.notified_milestones)

        # Calling again immediately should NOT trigger (already notified)
        res2 = evaluate_task_notifications(task, now)
        self.assertIsNone(res2)

    def test_due_now_trigger(self):
        now = datetime.datetime.now()
        # Task just passed deadline by 2 minutes
        past_2m = (now - datetime.timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
        task = Task(id=11, title="Pay bill", due_date=past_2m)

        res = evaluate_task_notifications(task, now)
        self.assertIsNotNone(res)
        milestone, urgency = res
        self.assertEqual(milestone, "due")
        self.assertEqual(urgency, "due")


if __name__ == "__main__":
    unittest.main()
