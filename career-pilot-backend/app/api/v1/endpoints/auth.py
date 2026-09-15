from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

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


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path=f"{settings.API_V1_PREFIX}/auth",
    )


def invalid_refresh_response() -> JSONResponse:
    # Raising an API exception loses mutations made to FastAPI's injected
    # response. Return this response directly so a rotated/revoked cookie is
    # actually removed from the browser and cannot trigger 401s forever.
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Authentication required"},
    )
    clear_refresh_cookie(response)
    return response


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
        return invalid_refresh_response()
    try:
        result = await AuthService(session).refresh(token, request.headers.get("user-agent"))
    except Exception as exc:
        from app.core.exceptions import AuthenticationError

        if isinstance(exc, AuthenticationError):
            return invalid_refresh_response()
        raise
    return token_response(response, result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, session: SessionDep):
    await AuthService(session).logout(request.cookies.get(settings.REFRESH_COOKIE_NAME))
    clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user
