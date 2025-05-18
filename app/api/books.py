from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.services.bookServices import BookService
from app.utils.decorators import token_required

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
@token_required
async def create_book(request: Request, book: BookService.BookCreate, db: AsyncSession = Depends(get_db)):
    return await BookService.create_book(book, db)

@router.get("/")
@token_required
async def list_books(request: Request, db: AsyncSession = Depends(get_db)):
    return await BookService.list_books(db)

@router.get("/recommendations")
@token_required
async def get_recommendations(request: Request, db: AsyncSession = Depends(get_db)):
    return await BookService.get_recommendations(request, db)

@router.get("/{book_id}")
@token_required
async def get_book(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    return await BookService.get_book(book_id, db)

@router.put("/{book_id}")
@token_required
async def update_book(request: Request, book_id: int, book: BookService.BookCreate, db: AsyncSession = Depends(get_db)):
    return await BookService.update_book(book_id, book, db)

@router.delete("/{book_id}")
@token_required
async def delete_book(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    return await BookService.delete_book(book_id, db)

@router.post("/{book_id}/reviews", status_code=status.HTTP_201_CREATED)
@token_required
async def add_review(request: Request, book_id: int, review: BookService.ReviewCreate, db: AsyncSession = Depends(get_db)):
    return await BookService.add_review(book_id, review, request, db)

@router.get("/{book_id}/reviews")
@token_required
async def get_reviews(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    return await BookService.get_reviews(book_id, db)

@router.get("/{book_id}/summary")
@token_required
async def get_book_summary(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    return await BookService.get_book_summary(book_id, db)

@router.post("/generate-summary")
@token_required
async def generate_summary(request: Request, content: BookService.SummaryCreate):
    return await BookService.generate_summary(content)

@router.post("/generate-summary-by-book-id/{book_id}")
@token_required
async def generate_summary_by_book_id(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    return await BookService.generate_summary_by_book_id(book_id, db)

@router.get("/generate-summary-by-book-name/{book_name}")
@token_required
async def generate_summary_by_book_name(request: Request, book_name: str, db: AsyncSession = Depends(get_db)):
    return await BookService.generate_summary_by_book_name(book_name)

