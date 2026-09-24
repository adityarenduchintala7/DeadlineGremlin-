import os
import sys
import winreg
from pathlib import Path
from typing import Tuple

STARTUP_SCRIPT_NAME = "TaskCheckerDaemon.vbs"
REGISTRY_KEY_NAME = "TaskCheckerDaemon"


def get_startup_folder() -> Path:
    """Returns the Windows User Startup folder."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    return Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def get_startup_file_path() -> Path:
    return get_startup_folder() / STARTUP_SCRIPT_NAME


def get_pythonw_path() -> str:
    """Returns path to pythonw.exe to run without terminal window."""
    py_exe = sys.executable
    if py_exe.endswith("python.exe"):
        pyw = py_exe[:-10] + "pythonw.exe"
        if os.path.exists(pyw):
            return pyw
    return py_exe


def get_main_script_path() -> str:
    return str(Path(__file__).parent / "main.py")


def enable_autostart() -> Tuple[bool, str]:
    """
    Configures Windows Startup to automatically launch the daemon
    upon system boot / user login.
    """
    pythonw = get_pythonw_path()
    main_script = get_main_script_path()
    cmd_args = f'"{pythonw}" "{main_script}" daemon run'

    success_messages = []

    # 1. Create silent VBScript in Startup folder
    try:
        startup_folder = get_startup_folder()
        startup_folder.mkdir(parents=True, exist_ok=True)
        vbs_path = get_startup_file_path()
        vbs_content = (
            'Set WshShell = CreateObject("WScript.Shell")\n'
            f'WshShell.Run chr(34) & "{pythonw}" & chr(34) & " " & chr(34) & "{main_script}" & chr(34) & " daemon run", 0, False\n'
        )
        vbs_path.write_text(vbs_content, encoding="utf-8")
        success_messages.append(f"Startup folder shortcut created at {vbs_path.name}")
    except Exception as e:
        pass

    # 2. Set Registry HKCU Run key
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, REGISTRY_KEY_NAME, 0, winreg.REG_SZ, cmd_args)
        winreg.CloseKey(key)
        success_messages.append("Windows Registry Run key registered")
    except Exception as e:
        pass

    if success_messages:
        return True, "Autostart enabled successfully: " + "; ".join(success_messages)
    return False, "Failed to enable autostart in Startup folder and Registry."


def disable_autostart() -> Tuple[bool, str]:
    """Removes autostart entries from Startup folder and Registry."""
    removed = []

    # 1. Remove VBScript from Startup folder
    vbs_path = get_startup_file_path()
    if vbs_path.exists():
        try:
            vbs_path.unlink()
            removed.append("Startup folder shortcut")
        except OSError:
            pass

    # 2. Remove Registry HKCU Run key
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, REGISTRY_KEY_NAME)
        winreg.CloseKey(key)
        removed.append("Registry Run key")
    except FileNotFoundError:
        pass
    except Exception:
        pass

    if removed:
        return True, "Autostart disabled. Removed: " + ", ".join(removed)
    return True, "Autostart was not enabled."


def is_autostart_enabled() -> bool:
    """Checks whether autostart is active in Startup folder or Registry."""
    if get_startup_file_path().exists():
        return True

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        _, _ = winreg.QueryValueEx(key, REGISTRY_KEY_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
