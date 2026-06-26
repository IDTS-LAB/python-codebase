from uuid import UUID

from pydantic import BaseModel


class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    domain: str | None = None

    model_config = {"from_attributes": True}
