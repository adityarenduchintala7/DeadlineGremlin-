import re
import datetime
from typing import Optional, Tuple


class DateParseError(ValueError):
    """Raised when user input cannot be parsed into a date/time."""
    pass


def parse_time_str(time_str: str) -> Tuple[int, int]:
    """Parse time string like '5pm', '5:30pm', '17:00', '9am', '14:30'."""
    s = time_str.strip().lower()
    
    # Check 12-hour format with am/pm (e.g. 5pm, 5:30pm, 11:45am)
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", s)
    if m:
        hr = int(m.group(1))
        mn = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)
        if hr < 1 or hr > 12 or mn < 0 or mn > 59:
            raise DateParseError(f"Invalid time format: {time_str}")
        if ampm == "pm" and hr != 12:
            hr += 12
        elif ampm == "am" and hr == 12:
            hr = 0
        return hr, mn

    # Check 24-hour format (e.g. 17:00, 09:30, 23:59)
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if m:
        hr = int(m.group(1))
        mn = int(m.group(2))
        if 0 <= hr <= 23 and 0 <= mn <= 59:
            return hr, mn
        raise DateParseError(f"Hour must be 0-23 and minute 0-59: {time_str}")

    raise DateParseError(f"Could not understand time format: '{time_str}'. Use e.g. '5pm', '17:30', '9:15am'.")


def parse_due_date(input_str: str) -> str:
    """
    Parses a wide variety of date/time expressions into a standard
    'YYYY-MM-DD HH:MM:SS' string.

    Supported patterns:
    - Relative offset: 'in 30 mins', 'in 2 hours', 'in 1d', 'in 3 days', 'in 2h 30m'
    - Today / Tomorrow: 'today 18:00', 'today 5pm', 'tomorrow 9am', 'tomorrow', 'tonight'
    - Specific weekday: 'monday 5pm', 'next friday 10am'
    - Standalone time: '18:00', '5pm' (today if future, else tomorrow)
    - Full ISO / Standard: '2026-09-25 15:30', '2026-09-25', '25-09-2026 15:30', 'Sep 25 5pm'
    """
    if not input_str or not input_str.strip():
        raise DateParseError("Deadline cannot be empty.")

    s = input_str.strip().lower()
    now = datetime.datetime.now()

    # 1. Relative offset: "in ..."
    # E.g. "in 30m", "in 45 minutes", "in 2h", "in 2 hours", "in 1 day", "in 2h 30m"
    if s.startswith("in "):
        rest = s[3:].strip()
        delta = datetime.timedelta()
        matched = False

        # Match parts like "1d", "2h", "30m", "45mins", "2 hours"
        tokens = re.findall(r"(\d+)\s*(days?|d|hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)", rest)
        if tokens:
            matched = True
            for val_str, unit in tokens:
                val = int(val_str)
                unit = unit.lower()
                if unit in ("d", "day", "days"):
                    delta += datetime.timedelta(days=val)
                elif unit in ("h", "hr", "hrs", "hour", "hours"):
                    delta += datetime.timedelta(hours=val)
                elif unit in ("m", "min", "mins", "minute", "minutes"):
                    delta += datetime.timedelta(minutes=val)
                elif unit in ("s", "sec", "secs", "second", "seconds"):
                    delta += datetime.timedelta(seconds=val)

        if matched and delta.total_seconds() > 0:
            target = now + delta
            return target.strftime("%Y-%m-%d %H:%M:%S")

    # 2. "tonight"
    if s == "tonight":
        target = now.replace(hour=21, minute=0, second=0, microsecond=0)
        if target <= now:
            target = now.replace(hour=23, minute=59, second=0, microsecond=0)
        return target.strftime("%Y-%m-%d %H:%M:%S")

    # 3. "today <time>"
    if s.startswith("today"):
        time_part = s.replace("today", "").strip()
        if not time_part:
            # Default to end of work day: 18:00
            target = now.replace(hour=18, minute=0, second=0, microsecond=0)
            if target <= now:
                target = now.replace(hour=23, minute=59, second=0, microsecond=0)
            return target.strftime("%Y-%m-%d %H:%M:%S")
        hr, mn = parse_time_str(time_part)
        target = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
        return target.strftime("%Y-%m-%d %H:%M:%S")

    # 4. "tomorrow" or "tomorrow <time>"
    if s.startswith("tomorrow"):
        time_part = s.replace("tomorrow", "").strip()
        tomorrow_date = now.date() + datetime.timedelta(days=1)
        if not time_part:
            target = datetime.datetime.combine(tomorrow_date, datetime.time(9, 0, 0))
            return target.strftime("%Y-%m-%d %H:%M:%S")
        hr, mn = parse_time_str(time_part)
        target = datetime.datetime.combine(tomorrow_date, datetime.time(hr, mn, 0))
        return target.strftime("%Y-%m-%d %H:%M:%S")

    # 5. Day of week: e.g. "friday 5pm", "next monday 10:00"
    weekdays = {
        "monday": 0, "mon": 0,
        "tuesday": 1, "tue": 1, "tues": 1,
        "wednesday": 2, "wed": 2,
        "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
        "friday": 4, "fri": 4,
        "saturday": 5, "sat": 5,
        "sunday": 6, "sun": 6
    }
    weekday_pattern = r"^(?:next\s+)?(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)(?:\s+(.+))?$"
    m_day = re.match(weekday_pattern, s)
    if m_day:
        day_name = m_day.group(1)
        time_part = m_day.group(2)
        target_weekday = weekdays[day_name]
        days_ahead = (target_weekday - now.weekday()) % 7
        if days_ahead == 0 and not time_part:
            days_ahead = 7
        target_date = now.date() + datetime.timedelta(days=days_ahead)
        if time_part:
            hr, mn = parse_time_str(time_part)
        else:
            hr, mn = 9, 0
        target = datetime.datetime.combine(target_date, datetime.time(hr, mn, 0))
        if target <= now and days_ahead == 0:
            target += datetime.timedelta(days=7)
        return target.strftime("%Y-%m-%d %H:%M:%S")

    # 6. Standalone time: "18:00", "5pm", "2:30pm"
    try:
        hr, mn = parse_time_str(s)
        target = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
        # If this time has already passed today, assume tomorrow at that time
        if target <= now:
            target += datetime.timedelta(days=1)
        return target.strftime("%Y-%m-%d %H:%M:%S")
    except DateParseError:
        pass

    # 7. Standard Date Formats
    date_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %I:%M%p",
        "%Y-%m-%d %I%p",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %I:%M %p",
        "%d-%m-%Y %I%p",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %I%p",
        "%d/%m/%Y",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
        "%b %d %Y %H:%M",
        "%b %d %Y %I:%M %p",
        "%b %d %H:%M",
        "%b %d %I:%M %p",
        "%b %d %I%p",
        "%B %d %Y %H:%M",
        "%B %d %H:%M",
    ]

    for fmt in date_formats:
        try:
            val_to_parse = input_str.strip()
            use_fmt = fmt
            if "%Y" not in fmt:
                val_to_parse = f"{now.year} {val_to_parse}"
                use_fmt = f"%Y {fmt}"
            dt = datetime.datetime.strptime(val_to_parse, use_fmt)
            if "%Y" not in fmt and dt < now:
                dt = dt.replace(year=now.year + 1)
            # If no time was included in format (defaults to 00:00:00), default to 23:59:00
            if "H" not in fmt and "I" not in fmt:
                dt = dt.replace(hour=23, minute=59, second=0)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    raise DateParseError(
        f"Unable to parse deadline: '{input_str}'.\n"
        "Supported examples:\n"
        "  Relative:   'in 30 mins', 'in 2 hours', 'in 3 days', 'in 1h 45m'\n"
        "  Keywords:   'today 6pm', 'tomorrow 9am', 'tonight', 'friday 5pm'\n"
        "  Time only:  '18:30', '5pm'\n"
        "  Full date:  '2026-09-25 17:00', '25-09-2026 5pm'"
    )
