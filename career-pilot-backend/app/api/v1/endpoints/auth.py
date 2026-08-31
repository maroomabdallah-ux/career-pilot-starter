from fastapi import APIRouter, Request, Response, status

from app.api.dependencies import CurrentUser, SessionDep
from app.core.config import settings
from app.schemas.auth import AccessTokenResponse, LoginRequest, SignupRequest
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter()


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path=f"{settings.API_V1_PREFIX}/auth",
    )


def token_response(response: Response, result) -> AccessTokenResponse:
    user, access_token, refresh_token = result
    set_refresh_cookie(response, refresh_token)
    return AccessTokenResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/signup", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(data: SignupRequest, request: Request, response: Response, session: SessionDep):
    return token_response(
        response, await AuthService(session).signup(data, request.headers.get("user-agent"))
    )


@router.post("/login", response_model=AccessTokenResponse)
async def login(data: LoginRequest, request: Request, response: Response, session: SessionDep):
    return token_response(
        response,
        await AuthService(session).login(
            str(data.email), data.password, request.headers.get("user-agent")
        ),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(request: Request, response: Response, session: SessionDep):
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not token:
        from app.core.exceptions import AuthenticationError

        raise AuthenticationError()
    return token_response(
        response, await AuthService(session).refresh(token, request.headers.get("user-agent"))
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: SessionDep):
    await AuthService(session).logout(request.cookies.get(settings.REFRESH_COOKIE_NAME))
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path=f"{settings.API_V1_PREFIX}/auth")


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user
