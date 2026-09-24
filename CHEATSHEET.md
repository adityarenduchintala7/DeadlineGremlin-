# 📑 DeadlineGremlin CLI Cheat Sheet

Quick terminal reference for **DeadlineGremlin** (`task`).

---

## ⚡ Quick Command Summary

| Command | Shorthand | Example | Description |
| :--- | :--- | :--- | :--- |
| `task add` | - | `task add "Buy milk" "in 2 hours"` | Add a new task with a deadline |
| `task list` | `task ls` | `task list` | List all active pending tasks |
| `task list -a` | `task ls -a` | `task list --all` | Show all tasks including completed |
| `task done` | `task complete`| `task done 1` | Mark task as finished (stops reminders) |
| `task undo` | - | `task undo 1` | Reopen a completed task |
| `task remove` | `task rm`, `task delete` | `task rm 1 2` | Permanently delete one or more tasks |
| `task edit` | - | `task edit 1 -d "tomorrow 5pm"` | Edit deadline, title, priority, or notes |
| `task clear` | - | `task clear` | Delete all completed tasks from storage |
| `task notify` | - | `task notify` | Check tasks & fire pending toasts now |
| `task test-notify` | - | `task test-notify` | Fire a test Windows toast notification |
| `task daemon start` | - | `task daemon start` | Launch background reminder service |
| `task daemon stop` | - | `task daemon stop` | Stop background reminder service |
| `task daemon status` | - | `task daemon status` | Check if background service is running |
| `task autostart enable` | - | `task autostart enable` | Resume reminders automatically on PC boot |
| `task install-path` | `task path` | `task install-path` | Add folder to Windows User PATH |

---

## ⏰ Supported Deadline Formats

You can specify deadlines using natural language or strict formats:

### 1. Relative Countdown
```powershell
task add "Take break" "in 15m"
task add "Submit report" "in 2 hours"
task add "Review PR" "in 1h 30m"
task add "Project milestone" "in 3 days"
```

### 2. Time Today / Tonight
```powershell
task add "Evening gym" "today 6pm"
task add "Client call" "today 17:30"
task add "Read book" "tonight"           # Defaults to 9:00 PM
task add "Quick check" "4:30pm"          # If future today, sets today; else rolls to tomorrow
```

### 3. Tomorrow & Weekdays
```powershell
task add "Team standup" "tomorrow 9am"
task add "Sprint planning" "tomorrow 14:00"
task add "Weekly review" "friday 5pm"
task add "Prep demo" "next monday 10am"
```

### 4. Calendar Dates
```powershell
task add "Tax filing" "2026-09-30 18:00"
task add "Dentist" "2026-10-15 11:30am"
task add "Anniversary" "25 Oct 6pm"
task add "End of month" "2026-09-30"     # Defaults to 23:59 end-of-day
```

---

## 🎨 Priority Badges & Options

Add priority with `-p` or `--priority`:
- `urgent` (🔴 Bright Red Bold)
- `high` (🔴 Red)
- `medium` (🟡 Yellow - default)
- `low` (🟢 Cyan / Green)

```powershell
task add "Fix critical server crash" "in 30 mins" -p urgent
task add "Water plants" "tomorrow 10am" -p low
```

Add optional notes with `-n` or `--notes`:
```powershell
task add "Prepare slides" "tomorrow 3pm" -p high -n "Use template from Q2"
```

---

## 🔔 How Notifications Work

DeadlineGremlin doesn't spam you every second. It calculates milestones:
1. **Long term**: Alerts at **48 hours** and **24 hours** remaining.
2. **Day of deadline**: Alerts at **12 hours**, **6 hours**, **3 hours**, **2 hours**, and **1 hour**.
3. **Crunch time**: Alerts at **30 minutes**, **15 minutes**, and **5 minutes**.
4. **Deadline reached**: **🚨 DUE NOW!** toast with chime.
5. **Overdue**: Gentle hourly nag alert until you mark `task done <id>`.

---

## 🔄 Moving or Renaming the Folder

Want to rename the folder (e.g. from `Trail` to `DeadlineGremlin`) or move it to `C:\Projects\DeadlineGremlin`?
1. **Rename / Move the folder** in Windows Explorer.
2. **Open the new folder** in Command Prompt or PowerShell.
3. **Run**:
   ```cmd
   setup.bat
   ```
   *(or run `task install-path` followed by `task autostart enable`)*.
4. **All your tasks are still there!** Tasks are stored in `~/.taskchecker/tasks.json`, so they are completely independent of where you put the project folder!

---

## ❓ Troubleshooting

- **No notifications appearing?**
  1. Check Windows **Focus Assist** / **Do Not Disturb** (in Windows Settings > System > Notifications). If "Do Not Disturb" is on, toasts are silenced into Action Center.
  2. Run `task test-notify` to test Windows toast integration.
  3. Run `task daemon status` to ensure the background monitor is running.
- **`task` command not found in a new terminal?**
  - Run `task install-path` once, then restart your terminal window.
