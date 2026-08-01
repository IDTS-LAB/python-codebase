from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(kw_only=True)
class RefreshToken:
    id: int | None = None
    user_id: int
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False

    @classmethod
    def create(
        cls, user_id: int, token_hash: str, expires_at: datetime
    ) -> RefreshToken:
        return cls(
            id=None,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )

    def revoke(self):
        self.is_revoked = True
