from abc import ABC, abstractmethod

from jose import JWTError
from starlette.requests import Request

from src.modules.api_key.application.service import ApiKeyService
from src.core.security.jwt import JWTService
from src.core.security.token_revocation import TokenRevocationService
from src.shared.exceptions.credential_exception import InvalidCredentialsError


class AuthenticationProvider(ABC):
    provider_name: str = ""

    @abstractmethod
    async def authenticate(self, token: str, request: Request) -> dict | None:
        ...


class JWTAuthProvider(AuthenticationProvider):
    provider_name = "jwt"

    async def authenticate(self, token: str, request: Request) -> dict | None:
        try:
            payload = JWTService.decode_token(token)
            JWTService.require_token_type(payload, JWTService.ACCESS_TOKEN_TYPE)
            if await TokenRevocationService.is_access_token_revoked(token):
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            request.state.token_payload = payload
            return {
                "user_id": user_id,
                "provider": self.provider_name,
                "payload": payload,
            }
        except (JWTError, InvalidCredentialsError, ValueError):
            return None


class ApiKeyAuthProvider(AuthenticationProvider):
    provider_name = "api_key"

    def __init__(self, api_key_service: ApiKeyService):
        self._api_key_service = api_key_service

    async def authenticate(self, token: str, request: Request) -> dict | None:
        api_key = await self._api_key_service.validate(token)
        if api_key is None:
            return None

        return {
            "user_id": str(api_key.id),
            "provider": self.provider_name,
            "payload": {
                "sub": str(api_key.id),
                "name": api_key.name,
                "permissions": api_key.permissions,
            },
        }
