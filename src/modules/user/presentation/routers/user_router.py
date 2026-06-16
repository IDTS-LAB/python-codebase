from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from core.security.jwt import JWTService
from core.security.password import PasswordSerrvice
from modules.user.application.create_user.command import CreateUserCommand
from modules.user.application.create_user.handler import CreateUserHandler
from modules.user.application.repository.user_repository import UserRepository
from modules.user.domain.exceptions.user_exception import UserAlreadyExistsError
from modules.user.presentation.dependencies import (
    get_current_user,
    get_register_handler,
    get_user_repository,
)
from modules.user.presentation.schemas.request import CreateUserRequest
from modules.user.presentation.schemas.response import TokenResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: CreateUserRequest,
    handler: CreateUserHandler = Depends(get_register_handler),
):
    try:
        command = CreateUserCommand(
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: UserRepository = Depends(get_user_repository),
):
    # TODO: need to move to query
    user = await repo.get_by_email(form_data.username)
    if not user or not PasswordSerrvice.verify_password(
        form_data.password, user.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = JWTService.create_access_token(data={"sub": str(user.id)})
    # TODO: move reponse to generic with schema
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    # TODO: move reponse to generic with schema
    return {"id": str(current_user.id), "email": current_user.email}
