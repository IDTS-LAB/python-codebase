from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ApiKey:
    id: UUID = field(default_factory=uuid4)
    key_prefix: str = ""
    key_hash: str = ""
    name: str = ""
    permissions: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    is_active: bool = True
    created_at: datetime | None = None
    last_used_at: datetime | None = None
