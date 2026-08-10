from datetime import datetime, time
import re


def validate_rating(value: int) -> int:
    if not 1 <= value <= 5:
        raise ValueError("Rating must be between 1 and 5")
    return value


def parse_time(value: str | time) -> time:
    if isinstance(value, time):
        return value
    if not isinstance(value, str):
        raise ValueError("Time must be a string or time value")

    text = value.strip().upper().replace(" ", "")
    formats = ["%I:%M%p", "%I%p", "%H:%M:%S", "%H:%M", "%H"]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    raise ValueError(
        "Time format must be one of: 9AM, 9:00AM, 9pm, 9:30pm, 09:00, 21:30, or a standard time string"
    )


def parse_duration(value: str | int) -> int:
    if isinstance(value, int):
        if value <= 0:
            raise ValueError("Duration must be greater than 0 minutes")
        return value
    if not isinstance(value, str):
        raise ValueError("Duration must be an integer or string like 30min, 1hr, or 1hr 30min")

    text = value.strip().lower()
    if not text:
        raise ValueError("Duration must not be empty")

    # accept values like 30min, 1hr, 1hr 30min, 90m, 2 h, 1 h 30 m
    pattern = re.compile(r"^(?:(?P<hours>\d+)\s*(?:h|hr|hrs))?\s*(?:(?P<minutes>\d+)\s*(?:m|min|mins))?$")
    match = pattern.match(text)
    if not match:
        raise ValueError("Duration format must be like 30min, 1hr, or 1hr 30min")

    hours = int(match.group("hours")) if match.group("hours") else 0
    minutes = int(match.group("minutes")) if match.group("minutes") else 0
    total = hours * 60 + minutes
    if total <= 0:
        raise ValueError("Duration must be greater than 0 minutes")
    return total


def format_duration(minutes: int) -> str:
    if minutes <= 0:
        raise ValueError("Duration must be greater than 0 minutes")
    hours, mins = divmod(minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}hr" if hours == 1 else f"{hours}hr")
    if mins:
        parts.append(f"{mins}min")
    return " ".join(parts) if parts else "0min"
