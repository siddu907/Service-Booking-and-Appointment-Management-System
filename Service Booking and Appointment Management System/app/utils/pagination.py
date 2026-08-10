from typing import Any


def paginate(items: list[Any], skip: int, limit: int):
    return items[skip: skip + limit]
