from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ==========================================
# 1. Standard Success Response
# ==========================================
class SuccessResponse(BaseModel, Generic[T]):
    success: bool = Field(
        default=True, description="Indicates if the request was successful"
    )
    message: str = Field(
        default="Operation successful", description="Human-readable message"
    )
    data: Optional[T] = Field(default=None, description="The actual response payload")


# ==========================================
# 2. Paginated Response
# ==========================================
class PaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items in the database")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="True if there is a next page")
    has_prev: bool = Field(..., description="True if there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True)
    message: str = Field(default="Paginated data retrieved successfully")
    meta: PaginationMeta
    data: List[T]


# ==========================================
# Cursor-Based Pagination
# ==========================================
class CursorMeta(BaseModel):
    next_cursor: Optional[str] = Field(
        default=None, description="Cursor for the next page. None if no more items."
    )
    prev_cursor: Optional[str] = Field(
        default=None, description="Cursor for the previous page. None if at the start."
    )
    has_next: bool = Field(
        ..., description="True if there are more items after this page"
    )
    has_prev: bool = Field(..., description="True if there are items before this page")
    limit: int = Field(..., description="Number of items per page")


class CursorPaginatedResponse(BaseModel, Generic[T]):
    success: bool = Field(default=True)
    message: str = Field(default="Cursor-paginated data retrieved successfully")
    meta: CursorMeta
    data: List[T]


# ==========================================
# 3. Standard Error Response
# ==========================================
class ErrorDetail(BaseModel):
    field: Optional[str] = Field(
        default=None, description="The field that caused the error (for validation)"
    )
    message: str = Field(..., description="Specific error message for this field/issue")


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: dict = Field(..., description="Error details")

    @classmethod
    def create(
        cls,
        code: str,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
        http_status: int = 400,
    ) -> tuple:
        """
        Helper to create an ErrorResponse and return it with the correct HTTP status code.
        Returns: (ErrorResponse, http_status)
        """
        error_payload = {
            "code": code,
            "message": message,
            "details": [d.model_dump() for d in details] if details else None,
        }
        # Remove null details to keep JSON clean
        if error_payload["details"] is None:
            del error_payload["details"]

        return cls(error=error_payload), http_status
