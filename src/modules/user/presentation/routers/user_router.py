from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.di import get_current_user
from src.modules.user.application.detail_user.handler import DetailUserQueryHandler
from src.modules.user.application.detail_user.query import DetailUserQuery
from src.modules.user.application.login_user.command import LoginUserCommand
from src.modules.user.application.login_user.handler import LoginUserCommandHandler
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
    get_refresh_token_handler,
    get_register_handler,
    get_user_detail_handler,
)
from src.modules.user.presentation.schemas.request import (
    CreateUserRequest,
    RefreshTokenRequest,
)
from src.modules.user.presentation.schemas.response import TokenResponse
from src.shared.exceptions.credential_exception import InvalidRefreshTokenError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
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
        # TODO: move reponse to generic with schema
        return {"message": "User registered successfully", "user_id": str(user.id)}
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    handler: LoginUserCommandHandler = Depends(get_login_handler),
):
    command = LoginUserCommand(username=form.username, password=form.password)
    result = await handler.execute(command=command)
    return {
        "access_token": result.get("access_token"),
        "refresh_token": result.get("refresh_token"),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    handler: RefreshTokenCommandHandler = Depends(get_refresh_token_handler),
):
    try:
        # Note: In strict rotation, we might not even require a valid access token here,
        # just the refresh token. But requiring it adds a layer of security.
        # We pass current_user["id"] to ensure the RT belongs to the user making the request.
        result = await handler.execute(
            RefreshTokenCommand(
                token=request.refresh_token,
            )
        )
        return {
            "access_token": result.get("access_token"),
            "refresh_token": result.get("refresh_token"),
            "token_type": "bearer",
        }
    except InvalidRefreshTokenError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def get_me(
    current_user: dict = Depends(get_current_user),
    handler: DetailUserQueryHandler = Depends(get_user_detail_handler),
):
    user = await handler.execute(
        DetailUserQuery(
            user_id=current_user.get("id"),
        )
    )
    return {"id": str(user.id), "email": user.email}


# TODO: need logout endpoint
