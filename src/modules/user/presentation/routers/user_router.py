from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.authorization.dependencies import require_permission
from src.core.authorization.permissions import (
    ME_ACTION,
    UPDATE_ACTION,
    USER_RESOURCE,
)
from src.core.schemas.response import SuccessResponse
from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.application.login_user.command import LoginUserCommand
from src.modules.user.application.login_user.handler import LoginUserCommandHandler
from src.modules.user.application.logout_user.command import LogoutUserCommand
from src.modules.user.application.logout_user.handler import LogoutUserCommandHandler
from src.modules.user.application.refresh_token.command import RefreshTokenCommand
from src.modules.user.application.refresh_token.handler import (
    RefreshTokenCommandHandler,
)
from src.modules.user.application.register_user.command import RegisterUserCommand
from src.modules.user.application.register_user.handler import (
    RegisterUserCommandHandler,
)
from src.modules.user.domain.exceptions.user_exception import UserAlreadyExistsError
from src.modules.user.presentation.dependency import (
    get_login_handler,
    get_logout_handler,
    get_refresh_token_handler,
    get_register_handler,
    get_user_detail_handler,
)
from src.modules.user.presentation.schemas.request import (
    CreateUserRequest,
    RefreshTokenRequest,
)
from src.modules.user.presentation.schemas.response import TokenResponse, UserResponse
from src.shared.exceptions.credential_exception import InvalidRefreshTokenError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=SuccessResponse[UserResponse],
)
async def register(
    request: CreateUserRequest,
    handler: RegisterUserCommandHandler = Depends(get_register_handler),
):
    try:
        command = RegisterUserCommand(
            email=request.username,
            password=request.password,
        )
        user = await handler.execute(command)
        return SuccessResponse(
            message="User registered successfully",
            data=UserResponse(
                id=user.id,
                email=user.email,
            ),
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=SuccessResponse[TokenResponse])
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    handler: LoginUserCommandHandler = Depends(get_login_handler),
):
    command = LoginUserCommand(username=form.username, password=form.password)
    result = await handler.execute(command=command)
    return SuccessResponse(
        message="Login success",
        success=True,
        data=TokenResponse(
            access_token=result.get("access_token"),
            refresh_token=result.get("refresh_token"),
            token_type="bearer",
        ),
    )


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    handler: RefreshTokenCommandHandler = Depends(get_refresh_token_handler),
):
    try:
        result = await handler.execute(
            RefreshTokenCommand(
                token=request.refresh_token,
            )
        )
        return SuccessResponse(
            message="Refresh token success",
            success=True,
            data=TokenResponse(
                access_token=result.get("access_token"),
                refresh_token=result.get("refresh_token"),
                token_type="bearer",
            ),
        )
    except InvalidRefreshTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=SuccessResponse[UserResponse])
async def get_me(
    current_user: dict = Depends(require_permission(USER_RESOURCE, ME_ACTION)),
    handler: DetailUserQueryHandler = Depends(get_user_detail_handler),
):
    user = await handler.execute(
        DetailUserQuery(
            user_id=current_user.get("id"),
        )
    )
    return SuccessResponse(
        success=True,
        message="fetch user data success",
        data=UserResponse(
            id=str(user.id),
            email=user.email,
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: dict = Depends(require_permission(USER_RESOURCE, UPDATE_ACTION)),
    handler: LogoutUserCommandHandler = Depends(get_logout_handler),
):
    auth_header = request.headers.get("Authorization", "")
    access_token = auth_header.removeprefix("Bearer ").strip()
    await handler.execute(
        LogoutUserCommand(
            user_id=str(current_user.get("id")),
            access_token=access_token,
        )
    )
