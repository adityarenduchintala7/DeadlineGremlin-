# 👾 DeadlineGremlin

> **"Because future you is already tired of present you's excuses."**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078D6.svg?logo=windows)](https://microsoft.com/windows)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg?logo=python)](https://python.org)
[![Shell: PowerShell%20%7C%20CMD](https://img.shields.io/badge/Shell-PowerShell%20%7C%20CMD-5391FE.svg)](https://github.com)

A relentless, lightweight, terminal-based task checker and deadline nagger for Windows. It quietly lives in your terminal and sends native Windows desktop toast notifications with audio chimes as your deadlines approach — **even after you shut down and reboot your computer**.

```text
       \   /
       .-.-.       [ ⏰ DEADLINE GREMLIN ]
      ( o.o )  <-- "Did you finish that report yet?"
       > ^ <
     (___~___)
```

📚 **Quick Documentation Links:**
- 🔰 **[Beginner's Step-by-Step Guide (HOW_TO_USE.md)](HOW_TO_USE.md)** — Never used terminal before? Start here!
- 📑 **[CLI Quick Reference & Cheatsheet (CHEATSHEET.md)](CHEATSHEET.md)** — All commands, flags, and date expressions.

---

## ⚡ Why DeadlineGremlin?

Most to-do apps require opening a heavy browser tab, signing up for an account, or waiting 10 seconds for an Electron app to launch.

**DeadlineGremlin** is designed for developers, hackers, and terminal lovers:
- **Instant**: Add a task in 2 seconds right from PowerShell or Command Prompt.
- **Natural Language**: Type deadlines like `"in 2 hours"`, `"tomorrow 9am"`, or `"tonight"`.
- **Persistent Across Reboots**: Shut down your laptop for the weekend? When you boot back up on Monday, your tasks and background reminders are right where you left them.
- **Smart Nagging**: Alerts you at milestone intervals (24h, 12h, 6h, 3h, 2h, 1h, 30m, 15m, 5m, when due, and periodic overdue nags).
- **Zero External Python Dependencies**: Built purely with Python standard library and native Windows WinRT APIs.

---

## 🚀 Quick Start (1 Minute)

### 1. Installation
Run the one-click setup script in this folder:
```cmd
setup.bat
```
This automatically:
1. Adds `task` to your Windows User `PATH` (works from any folder).
2. Sets up autostart across Windows reboots.
3. Launches the background notification monitor.

### 2. Add Your First Task
```powershell
task add "Submit quarterly report" "tomorrow 5pm" --priority high
```

### 3. Check Your Tasks
```powershell
task list
```

**Output:**
```
ID   PRIORITY  DEADLINE           TIME LEFT / STATUS       TITLE
#1   [HIGH]    Sep 25 05:00PM     ⏰ in 28h 15m             Submit quarterly report

Summary: 1 pending  |  Notifier: ● Active
```

---

## 💻 Commands Overview

| Command | Shorthand | What it does |
| :--- | :--- | :--- |
| `task add "<title>" "<due>"` | - | Add a new task with a deadline |
| `task list` | `task ls` | Show active pending tasks |
| `task list --all` | `task ls -a` | Show all tasks (including completed) |
| `task done <id>` | `task complete` | Mark task complete (stops notifications) |
| `task undo <id>` | - | Reopen a completed task |
| `task remove <id>` | `task rm` | Permanently delete a task |
| `task edit <id> [flags]` | - | Edit title, deadline, priority, or notes |
| `task clear` | - | Delete completed tasks from storage |
| `task notify` | - | Force a notification check right now |
| `task test-notify` | - | Test desktop toast notifications |
| `task daemon start/stop/status` | - | Manage background monitoring daemon |
| `task autostart enable/disable` | - | Toggle auto-launch on PC boot |
| `task install-path` | - | Register folder in Windows PATH |

👉 **For the full command cheatsheet with all date formats, see [CHEATSHEET.md](CHEATSHEET.md)!**

---

## ⏰ Flexible Deadline Formats

You don't need to remember complex date formats. DeadlineGremlin understands:

```powershell
# Relative times:
task add "Take a screen break" "in 25m"
task add "Review pull request" "in 2 hours"
task add "Submit project" "in 3 days"

# Human expressions:
task add "Team standup" "tomorrow 9am"
task add "Finish gym session" "today 6:30pm"
task add "Read novel chapter" "tonight"
task add "Weekly sync" "friday 4pm"

# Specific dates:
task add "Tax filing deadline" "2026-09-30 18:00" -p urgent
task add "Dentist visit" "15 Oct 10:30am"
```

---

## 🔔 How Milestone Reminders Work

DeadlineGremlin doesn't spam you every minute. Instead, it evaluates progressive urgency milestones:

```text
  [48h & 24h] ---> [12h / 6h / 3h] ---> [2h / 1h] ---> [30m / 15m / 5m] ---> [🚨 DUE NOW!]
   Long-term         Day-of Alert       Final Hours       Crunch Time          Deadline
```

- When deadline is reached: Fires a high-priority toast: `🚨 DUE NOW: <Task>`.
- If a task is overdue: Sends gentle periodic reminders every 1-2 hours until you mark it `task done <id>`.
- Offline recovery: If your PC was turned off when a milestone passed, when you turn your PC on, DeadlineGremlin automatically calculates the current time left and notifies you with the most urgent current alert.

---

## 📁 Architecture & File Structure

```text
DeadlineGremlin/
├── taskchecker/              # Core Python package
│   ├── cli.py               # Terminal interface (colors, table formatting, arguments)
│   ├── models.py            # Task data model & time calculations
│   ├── date_parser.py       # Natural language date/time parser
│   ├── storage.py           # Safe atomic JSON storage manager
│   ├── notifier.py          # Windows toast caller & chime generator
│   ├── daemon.py            # Background monitor process & milestone engine
│   ├── autostart.py         # Windows Startup folder & Registry manager
│   └── toast.ps1            # WinRT PowerShell toast notification script
├── tests/                   # Test suite
│   └── test_all.py          # Unit tests (models, parser, storage, milestones)
├── task.bat                 # CMD launcher
├── task.ps1                 # PowerShell launcher
├── setup.bat                # 1-click installer
├── CHEATSHEET.md            # Quick reference guide
├── LICENSE                  # MIT License
└── pyproject.toml           # Packaging metadata
```

---

## 💾 Where are Tasks Stored?

Tasks are stored in your Windows user profile:
```text
%USERPROFILE%\.taskchecker\tasks.json
```
Because storage is located in your user profile:
- You can **rename** or **move** the `DeadlineGremlin` folder anywhere you want without losing any tasks!
- You can invoke `task` from any directory or drive (`C:\`, `D:\`, Desktop, etc.) and always see the same tasks.

---

## 🔄 Renaming or Moving This Folder

1. Rename or move the folder to your preferred location (e.g. `C:\Users\username\Projects\DeadlineGremlin`).
2. Run `setup.bat` (or `task install-path` and `task autostart enable`).
3. That's it! Your tasks and background reminders will seamlessly continue.

---

## 🧪 Running Tests

```powershell
python -m unittest tests/test_all.py
```

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
