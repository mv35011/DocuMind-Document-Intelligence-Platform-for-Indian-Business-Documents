from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from documind.core.security import TokenPayload, UserRole, decode_access_token
from documind.db.session import async_session_factory, set_workspace_rls

security_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenPayload:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Defense in depth: Set transaction-local PostgreSQL RLS workspace context
    await set_workspace_rls(session, payload.workspace_id)
    return payload


def require_role(min_role: UserRole):
    role_hierarchy = {UserRole.VIEWER: 1, UserRole.REVIEWER: 2, UserRole.ADMIN: 3}

    async def role_checker(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
        if role_hierarchy.get(user.role, 0) < role_hierarchy.get(min_role, 0):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires minimum role '{min_role.value}', you have '{user.role.value}'",
            )
        return user

    return role_checker
