from datetime import datetime


def now() -> datetime:
    return datetime.utcnow()


def parse_duration_to_minutes(duration: str) -> int:
    """Parse duration strings like '1hr 30min', '45min', '2hr' into total minutes."""
    if duration is None:
        raise ValueError("Duration is required")
    s = duration.strip().lower()
    hours = 0
    minutes = 0
    # split by spaces
    parts = s.replace(',', ' ').split()
    for part in parts:
        if part.endswith('hr') or part.endswith('hrs'):
            try:
                hours += int(part.replace('hrs', '').replace('hr', ''))
            except ValueError:
                raise ValueError(f"Invalid hours value in duration: {part}")
        elif part.endswith('min') or part.endswith('mins'):
            try:
                minutes += int(part.replace('mins', '').replace('min', ''))
            except ValueError:
                raise ValueError(f"Invalid minutes value in duration: {part}")
        else:
            # allow plain number interpreted as minutes
            try:
                minutes += int(part)
            except ValueError:
                raise ValueError(f"Invalid duration segment: {part}")
    total = hours * 60 + minutes
    if total <= 0:
        raise ValueError("Duration must be greater than zero")
    return total


def format_minutes_to_duration(total: int) -> str:
    """Format total minutes into strings like '1hr 30min' or '45min' or '2hr'."""
    if total is None:
        return None
    hrs = total // 60
    mins = total % 60
    parts = []
    if hrs:
        parts.append(f"{hrs}hr")
    if mins:
        parts.append(f"{mins}min")
    return " ".join(parts) if parts else "0min"


def uploads_path_to_url(base_url: str, internal_path: str) -> str | None:
    """Convert an internal uploads path like '/uploads/profile_images/file.jpg'
    to a public URL under the static mount '/uploads/files/...'.

    Returns None if internal_path is falsy.
    """
    if not internal_path:
        return None
    from urllib.parse import quote

    if not internal_path.startswith("/uploads"):
        return internal_path
    path_part = "/uploads/files" + internal_path[len("/uploads") :]
    encoded = quote(path_part, safe="/")
    return f"{base_url.rstrip('/')}{encoded}"
