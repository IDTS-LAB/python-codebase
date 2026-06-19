import base64
import json
from datetime import datetime
from enum import Enum
from uuid import UUID


class CursorDirection(Enum):
    DIRECTION_NEXT = "next"
    DIRECTION_PREV = "prev"


def encode_cursor(created_at: datetime, id: UUID, dir: CursorDirection) -> str:
    """
    Encode a cursor from timestamp and ID.
    Format: base64(json({"t": "ISO_TIMESTAMP", "id": "UUID"}))
    """
    cursor_data = {"t": created_at.isoformat(), "id": str(id), "dir": dir.value}
    json_str = json.dumps(cursor_data)
    return base64.urlsafe_b64encode(json_str.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID, CursorDirection]:
    """
    Decode a cursor back to timestamp and ID.
    Returns: (created_at, id)
    """
    try:
        json_str = base64.urlsafe_b64decode(cursor.encode()).decode()
        cursor_data = json.loads(json_str)
        created_at = datetime.fromisoformat(cursor_data["t"])
        dir = CursorDirection(cursor_data["dir"])
        id = UUID(cursor_data["id"])
        return created_at, id, dir
    except Exception as e:
        raise ValueError(f"Invalid cursor format: {e}")
