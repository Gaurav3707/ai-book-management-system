from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.utils.jwt import create_access_token
from pydantic import BaseModel
from app.utils.messages.userMessages import (
    USER_REGISTERED_SUCCESS, USER_LOGIN_SUCCESS, INVALID_CREDENTIALS,
    USERNAME_ALREADY_REGISTERED, USER_PROFILE_RETRIEVED_SUCCESS
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

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
        logger.info(f"Attempting to register user: {user.username}")
        result = await db.execute(select(User).where(User.username == user.username))
        db_user = result.scalars().first()
        if db_user:
            logger.warning(f"Username already registered: {user.username}")
            return {"data": None, "status": 400, "message": USERNAME_ALREADY_REGISTERED}
        try:
            new_user = User(username=user.username, email=user.email, password=user.password)
            new_user.hash_password()
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            logger.info(f"User registered successfully: {user.username}")
            return {"data": None, "status": 201, "message": USER_REGISTERED_SUCCESS}
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise

    @staticmethod
    async def login_user(user: UserLogin, db: AsyncSession):
        logger.info(f"Attempting to log in user: {user.username}")
        result = await db.execute(select(User).where(User.username == user.username))
        db_user = result.scalars().first()
        if not db_user or not db_user.verify_password(user.password):
            logger.warning(f"Invalid credentials for user: {user.username}")
            return {"data": None, "status": 400, "message": INVALID_CREDENTIALS}
        token = create_access_token({"sub": db_user.username, "role": db_user.role, "user_id": db_user.id, "email": db_user.email})
        logger.info(f"User logged in successfully: {user.username}")
        return {"data": {"access_token": token, "token_type": "bearer"}, "status": 200, "message": USER_LOGIN_SUCCESS}

    @staticmethod
    async def get_user_profile(user: dict):
        logger.info(f"Fetching profile for user: {user['sub']}")
        data = {"username": user["sub"], "role": user["role"]}
        logger.debug(f"Profile data: {data}")
        return {"data": data, "status": 200, "message": USER_PROFILE_RETRIEVED_SUCCESS}
