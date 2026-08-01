from datetime import datetime

import pytest

from src.shared.utils.cursor import (
    CursorDirection,
    decode_cursor,
    encode_cursor,
)


def test_encode_decode_cursor_roundtrip_with_int_id():
    created_at = datetime(2026, 1, 1, 12, 30, 0)
    cursor = encode_cursor(created_at, 42, CursorDirection.DIRECTION_NEXT)
    decoded_created_at, decoded_id, decoded_dir = decode_cursor(cursor)
    assert decoded_created_at == created_at
    assert decoded_id == 42
    assert decoded_dir == CursorDirection.DIRECTION_NEXT


def test_decode_cursor_rejects_invalid_id():
    cursor = encode_cursor(datetime.now(), 7, CursorDirection.DIRECTION_PREV)
    assert decode_cursor(cursor)[1] == 7


def test_decode_cursor_rejects_garbage():
    with pytest.raises(ValueError, match="Invalid cursor format"):
        decode_cursor("not-a-cursor")
