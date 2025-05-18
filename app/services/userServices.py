from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.user import User
from app.utils.jwt import create_access_token
from pydantic import BaseModel

class UserService:
    class UserCreate(BaseModel):
        username: str
        email: str
        password: str

    class UserLogin(BaseModel):
        username: str
        password: str

    @staticmethod
    async def register_user(user: UserCreate, db: AsyncSession):
        result = await db.execute(select(User).where(User.username == user.username))
        db_user = result.scalars().first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        new_user = User(username=user.username, email=user.email, password=user.password)
        new_user.hash_password()
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {"data":None, "status":201, "message": "User registered successfully"}

    @staticmethod
    async def login_user(user: UserLogin, db: AsyncSession):
        result = await db.execute(select(User).where(User.username == user.username))
        db_user = result.scalars().first()
        if not db_user or not db_user.verify_password(user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        token = create_access_token({"sub": db_user.username, "role": db_user.role, "user_id": db_user.id, "email": db_user.email})
        return {"data":{"access_token": token, "token_type": "bearer"}, "status": 200, "message": "Login successful"}

    @staticmethod
    async def get_user_profile(user: dict):
        data =  {"username": user["sub"], "role": user["role"]}
        return {"data": data, "status": 200, "message": "User profile retrieved successfully"}
