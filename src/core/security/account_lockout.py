from datetime import datetime, timedelta, timezone
from typing import Protocol

from src.core.config.setting import Settings, get_settings


class LoginAttemptRepository(Protocol):
    async def count_failures_since(self, email: str, since: datetime) -> int:
        pass

    async def record_failure(
        self,
        email: str,
        occurred_at: datetime,
        locked_until: datetime | None = None,
    ) -> None:
        pass

    async def get_locked_until(self, email: str) -> datetime | None:
        pass

    async def clear(self, email: str) -> None:
        pass


class AccountLockoutService:
    def __init__(
        self,
        repository: LoginAttemptRepository | None = None,
        settings: Settings | None = None,
    ):
        self._repository = repository
        self._settings = settings or get_settings()

    async def ensure_login_allowed(self, email: str) -> None:
        if self._repository is None:
            return

        locked_until = await self._repository.get_locked_until(email)
        if locked_until and locked_until > datetime.now(timezone.utc):
            raise ValueError("Account is temporarily locked")

    async def record_failed_login(self, email: str) -> None:
        if self._repository is None:
            return

        now = datetime.now(timezone.utc)
        since = now - timedelta(minutes=self._settings.ACCOUNT_LOCKOUT_WINDOW_MINUTES)
        recent_failures = await self._repository.count_failures_since(email, since)

        locked_until = None
        if recent_failures + 1 >= self._settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
            locked_until = now + timedelta(
                minutes=self._settings.ACCOUNT_LOCKOUT_DURATION_MINUTES
            )

        await self._repository.record_failure(email, now, locked_until)

    async def record_successful_login(self, email: str) -> None:
        if self._repository is None:
            return

        await self._repository.clear(email)
