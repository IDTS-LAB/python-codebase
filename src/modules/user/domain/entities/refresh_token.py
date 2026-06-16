from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class RefreshToken:
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False

    @classmethod
    def create(
        cls, user_id: UUID, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        return cls(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )

    def revoke(self):
        self.is_revoked = True
