# 🔰 Beginner's Guide: How to Use DeadlineGremlin

Welcome to **DeadlineGremlin**! If you have never used a command-line tool before or you just want a simple, step-by-step walkthrough without technical jargon, this guide is for you.

---

## 🧭 Step 0: What is DeadlineGremlin?

DeadlineGremlin is a personal deadline assistant that lives in your computer. You give it tasks and due dates (like `"in 2 hours"` or `"tomorrow 5pm"`). 

As the deadline approaches, it automatically pops up **Windows desktop notifications with sound** to remind you, so you never forget an assignment, meeting, or chore — **even if you shut down and reboot your computer**.

---

## 🛠️ Step 1: One-Time Quick Setup

You only need to do this once:

1. Open this folder in Windows File Explorer.
2. Find the file named **`setup.bat`**.
3. **Double-click `setup.bat`**.

A black window will pop up for a couple of seconds, configure everything automatically, and then say `Setup Complete!`. Press any key to close it.

> 🎉 **That's it!** You can now use the `task` command from anywhere on your PC!

---

## 💻 Step 2: How to Open the Terminal

You can open a terminal in any of these simple ways:
- **Option A**: Press `Windows Key + R`, type `cmd` (or `powershell`), and press `Enter`.
- **Option B**: Press the `Windows Key`, search for **Terminal** (or **PowerShell** or **Command Prompt**), and open it.

---

## ✍️ Step 3: Adding Your First Task

To add a task, simply type `task add "Your Task Description" "When it is due"` and press `Enter`.

### Examples you can try right now:

```powershell
# In a few minutes or hours:
task add "Drink a glass of water" "in 15m"
task add "Submit assignment" "in 2 hours"

# Later today:
task add "Evening workout" "today 6:30pm"
task add "Read a chapter" "tonight"

# Tomorrow or later this week:
task add "Team standup meeting" "tomorrow 9am"
task add "Weekly review" "friday 5pm"

# Specific dates:
task add "File tax documents" "2026-09-30 18:00"
```

### Adding Priority (Optional):
You can tag tasks as `urgent`, `high`, `medium`, or `low`:
```powershell
task add "Fix critical website error" "in 30 mins" --priority urgent
task add "Call mom" "tomorrow 5pm" --priority high
task add "Organize desk" "today 8pm" --priority low
```

---

## 📋 Step 4: Seeing All Your Tasks

Whenever you want to see what is due, just type:
```powershell
task list
```
*(or simply `task ls`)*

You will see a clean, color-coded list:
- 🔴 **Red & Bold**: Overdue or due in less than an hour!
- 🟡 **Yellow**: Due later today!
- 🟢 **Green**: Due in the future!

### To see tasks you already finished:
```powershell
task list --all
```

---

## 🔔 Step 5: How Notifications Work

You **do not** need to keep your terminal window open. You can close it!

A silent background helper runs quietly in Windows and sends native desktop toast alerts at progressive milestones:
- **48 hours and 24 hours** before deadline
- **12h, 6h, 3h, 2h, and 1h** before deadline
- **30m, 15m, and 5m** (crunch time!)
- **🚨 DUE NOW!** when the exact time arrives
- If you miss the deadline, it will periodically remind you that it's overdue until you complete it.

> 💡 **Test your notifications right now**:
> Type: `task test-notify` and press `Enter`. You should see a notification pop up in the bottom-right corner of your screen!

---

## ✅ Step 6: Completing a Task

When you finish a task, find its ID number from `task list` (for example, `#1`) and type:
```powershell
task done 1
```
*(or `task complete 1`)*

This immediately turns off all future notifications for that task.

Accidentally marked it done? You can reopen it anytime:
```powershell
task undo 1
```

---

## 🗑️ Step 7: Deleting Tasks

To permanently delete a task you don't need anymore:
```powershell
task rm 1
```
*(or `task remove 1`)*

To clear out all old completed tasks:
```powershell
task clear
```

---

## 🔄 Step 8: What Happens When I Shut Down My Computer?

- **Your tasks are always saved**: They are securely stored on your drive, so turning off your PC will never lose them.
- **Auto-resumes on boot**: When you turn on or restart your PC, DeadlineGremlin automatically wakes up in the background and resumes monitoring your deadlines.

---

## ❓ Frequently Asked Questions (FAQ)

### 1. Do I need to keep the command prompt open?
**No!** Once you add a task, you can close the terminal completely. The background monitor handles all notifications.

### 2. Can I rename or move the project folder?
**Yes!** If you move or rename the folder, just double-click `setup.bat` once inside the new folder. All your existing tasks will still be there.

### 3. I didn't see a notification popup!
- Check if Windows **"Do Not Disturb"** or **"Focus Assist"** is turned on in Windows Settings. If enabled, Windows places notifications silently into the Action Center (notification bell in taskbar).
- Run `task test-notify` to test notifications.
- Run `task daemon status` to make sure the background monitor is running.

---

## 📖 Need a Quick Cheat Sheet?
Whenever you are in the terminal and forget a command, simply type:
```powershell
task cheatsheet
```
or open the file **[CHEATSHEET.md](CHEATSHEET.md)**.
