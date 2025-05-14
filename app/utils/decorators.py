from fastapi import HTTPException, Request
from functools import wraps
from app.utils.jwt import verify_access_token

def token_required(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        if not request:
            raise HTTPException(status_code=400, detail="Request object is missing")
        authorization: str = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization header is missing or invalid")
        token = authorization.split(" ")[1]
        payload = verify_access_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if 'user' in kwargs:
            kwargs['user'] = payload
        return await func(*args, **kwargs)
    return wrapper
