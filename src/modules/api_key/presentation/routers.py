from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.modules.api_key.application.service import ApiKeyService
from src.modules.api_key.domain.repository import ApiKeyRepository
from src.modules.api_key.presentation.dependencies import (
    get_api_key_repository,
    get_api_key_service,
)
from src.modules.api_key.presentation.schemas import (
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
    CreateApiKeyRequest,
)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post(
    "/",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    request: CreateApiKeyRequest,
    service: ApiKeyService = Depends(get_api_key_service),
):
    api_key, raw_key = await service.generate(
        name=request.name,
        permissions=request.permissions,
        expires_at=request.expires_at,
    )
    return ApiKeyCreatedResponse(
        id=str(api_key.id),
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        key=raw_key,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.get("/", response_model=ApiKeyListResponse)
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    repo: ApiKeyRepository = Depends(get_api_key_repository),
):
    items = await repo.list(skip=skip, limit=limit)
    total = await repo.count()
    return ApiKeyListResponse(
        items=[
            ApiKeyResponse(
                id=str(k.id),
                key_prefix=k.key_prefix,
                name=k.name,
                permissions=k.permissions,
                expires_at=k.expires_at,
                is_active=k.is_active,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
            )
            for k in items
        ],
        total=total,
    )


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: UUID,
    repo: ApiKeyRepository = Depends(get_api_key_repository),
):
    existing = await repo.get_by_id(api_key_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    await repo.revoke(api_key_id)
