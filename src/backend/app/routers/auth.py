from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import LoginRequest, LoginResponse, UserPublic
from app.services.auth_service import get_current_user_from_token, login

router = APIRouter()
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
def auth_login(body: LoginRequest) -> LoginResponse:
    result = login(body)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
        )
    return result


@router.get("/me", response_model=UserPublic)
def auth_me(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic:
    return get_authenticated_user(creds)


def get_authenticated_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UserPublic:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
        )
    user = get_current_user_from_token(creds.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
        )
    return user
