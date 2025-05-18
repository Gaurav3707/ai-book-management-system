from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config.settings import settings
from app.models import user as user_model
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from typing import Optional

http_bearer = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer), db: AsyncSession = Depends(get_db)) -> Optional[user_model.User]:
    """
    Retrieves the current user based on the provided JWT token.

    Args:
        credentials (HTTPAuthorizationCredentials): The authorization credentials containing the JWT token.
        db (AsyncSession): The database session.

    Returns:
        Optional[user_model.User]: The user object if the token is valid, otherwise None.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = await user_model.User.get_by_username(db, username=username)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user