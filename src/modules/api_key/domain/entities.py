from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ApiKey:
    id: int | None = None
    key_prefix: str = ""
    key_hash: str = ""
    name: str = ""
    permissions: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    last_used_at: datetime | None = None
