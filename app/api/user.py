from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.services.userServices import UserService
from app.utils.decorators import token_required

router = APIRouter()

@router.post("/register")
async def register(request: Request, user: UserService.UserCreate, db: AsyncSession = Depends(get_db)):
    return await UserService.register_user(user, db)

@router.post("/login")
async def login(request: Request, user: UserService.UserLogin, db: AsyncSession = Depends(get_db)):
    return await UserService.login_user(user, db)

@router.get("/profile")
@token_required
async def get_profile(request: Request, user: dict = None):
    return await UserService.get_user_profile(user)
