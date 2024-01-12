from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends

from src.core.container import Container
from src.core.dependencies import get_current_active_user
from src.schema.auth_schema import SignIn, SignInResponse, SignUp
from src.schema.user_schema import User, BaseUser, BaseUserWithBalance
from src.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/sign-in",
    response_model=SignInResponse,
    response_model_exclude_none=True,
    response_model_exclude={'user_info': {'password': True}}
)
@inject
async def sign_in(user_info: SignIn, service: AuthService = Depends(Provide[Container.auth_service])):
    return service.sign_in(user_info)


@router.post(
    "/sign-up",
    response_model=BaseUser,
    response_model_exclude_none=True,
    response_model_exclude={'password': True}
)
@inject
async def sign_up(user_info: SignUp, service: AuthService = Depends(Provide[Container.auth_service])):
    return service.sign_up(user_info)


@router.post(
    "/sign-up/debug_only",
    response_model=BaseUser,
    description="Returns superuser",
    response_model_exclude_none=True,
    response_model_exclude={'password': True}
)
@inject
async def sign_up_admin(user_info: SignUp, service: AuthService = Depends(Provide[Container.auth_service])):
    return service.sign_up(user_info, is_superuser=True)


@router.get(
    "/me", response_model=BaseUserWithBalance, response_model_exclude_none=True,
    response_model_exclude={'password': True}

)
@inject
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
