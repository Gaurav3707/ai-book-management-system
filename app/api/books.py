from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from app.models.database import get_db
from app.models.book import Book, Review 
from pydantic import BaseModel
from typing import List
import httpx, json
from app.config.settings import settings
from app.utils.decorators import token_required 
from app.utils.jwt import fetch_user_by_request
from app.utils.helper import convert_string_to_json


router = APIRouter()

# Pydantic models for request and response
class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    year_published: int
    summary: str

class SummaryCreate(BaseModel):
    content: str


class BookResponse(BookCreate):
    id: int

class ReviewCreate(BaseModel):
    review_text: str
    rating: int

class ReviewResponse(ReviewCreate):
    id: int
    user_id: int
    book_id: int

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
@token_required
async def create_book(request: Request, book: BookCreate, db: AsyncSession = Depends(get_db)):
    new_book = Book(**book.dict())
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return new_book

@router.get("/", response_model=List[BookResponse])
@token_required
async def list_books(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book))
    books = result.scalars().all()
    return books

@router.get("/recommendations")
@token_required
async def get_recommendations(request: Request, db: AsyncSession = Depends(get_db)):
    # Fetch highly rated books by the logged-in user
    user = fetch_user_by_request(request)
    result = await db.execute(select(Book).join(Review).where(Review.user_id == user['user_id'], Review.rating >= 4))
    highly_rated_books = result.scalars().all()

    # Prepare the list of books for the AI prompt
    highly_rated_books_list = [
        f"{book.title} by {book.author}" for book in highly_rated_books
    ]
    books_for_prompt = ", ".join(highly_rated_books_list) if highly_rated_books_list else "none"

    # AI prompt
    prompt = f"""<Instruction>
    <prompt>
        Based on the user's highly rated books: {books_for_prompt}, provide a list of 5 book recommendations with their titles and authors.
    </prompt>
    <responseFormat>
        <format>JSON</format>
        <guidelines>
            Ensure the output is in JSON format and follows this structure:
            {{
                "recommendations": [
                    {{
                        "title": "string",
                        "author": "string",
                        "genre": "string",
                        "year_published: "string",

                    }}
                ]
            }}
        </guidelines>
    </responseFormat>
</Instruction>
"""

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", settings.OLLAMA_ENDPOINT, json={
            "model": settings.AI_MODEL,
            "prompt": prompt
        }) as response:
            content = ""
            async for chunk in response.aiter_text():
                chunk = json.loads(chunk)
                content += chunk['response']

    data = await convert_string_to_json(content)
    return {"data": data}

@router.get("/{book_id}", response_model=BookResponse)
@token_required
async def get_book(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one()
        return book
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

@router.put("/{book_id}", response_model=BookResponse)
@token_required
async def update_book(request: Request, book_id: int, book: BookCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        existing_book = result.scalar_one()
        for key, value in book.model_dump().items():
            setattr(existing_book, key, value)
        db.add(existing_book)
        await db.commit()
        await db.refresh(existing_book)
        return existing_book
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
@token_required
async def delete_book(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one()
        await db.delete(book)
        await db.commit()
        return {"message": "Book deleted successfully"}
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

@router.post("/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
@token_required
async def add_review(request: Request, book_id: int, review: ReviewCreate, db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(select(Book).where(Book.id == book_id))
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    user = fetch_user_by_request(request)
    review = review.dict()
    review['user_id'] = user['user_id']
    new_review = Review(book_id=book_id, **review)
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review
    

@router.get("/{book_id}/reviews", response_model=List[ReviewResponse])
@token_required
async def get_reviews(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.book_id == book_id))
    reviews = result.scalars().all()
    return reviews

@router.get("/{book_id}/summary")
@token_required
async def get_book_summary(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one()
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    reviews_result = await db.execute(select(Review).where(Review.book_id == book_id))
    reviews = reviews_result.scalars().all()
    avg_rating = sum([review.rating for review in reviews]) / len(reviews) if reviews else 0
    return {
        "title": book.title,
        "author": book.author,
        "summary": book.summary,
        "average_rating": avg_rating,
        "total_reviews": len(reviews),
    }
    

@router.post("/generate-summary")
@token_required
async def generate_summary(request: Request, content: SummaryCreate):
    prompt = f"Provide a short summary for the following - {content.content}."

    # Collect the streamed response
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", settings.OLLAMA_ENDPOINT, json={
            "model": settings.AI_MODEL,
            "prompt": prompt
        }) as response:
            content = ""
            async for chunk in response.aiter_text():
                chunk = json.loads(chunk)
                content += chunk['response']

    return {"summary": content}


@router.post("/generate-summary-by-book-id/{book_id}")
@token_required
async def generate_summary_by_book_id(request: Request, book_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Book).where(Book.id == book_id))
        book = result.scalar_one()
    except NoResultFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    prompt = f"Provide a short summary for book - {book.title} by {book.author}."

    # Collect the streamed response
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", settings.OLLAMA_ENDPOINT, json={
            "model": settings.AI_MODEL,
            "prompt": prompt
        }) as response:
            content = ""
            async for chunk in response.aiter_text():
                chunk = json.loads(chunk)
                content += chunk['response']

    return {"book_id": book_id, "summary": content}

@router.get("/generate-summary-by-book-name/{book_name}")
@token_required
async def generate_summary_by_book_name(request: Request, book_name: str, db: AsyncSession = Depends(get_db)):
    prompt = f"Provide a short summary for book - {book_name}."

    # Collect the streamed response
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", settings.OLLAMA_ENDPOINT, json={
            "model": settings.AI_MODEL,
            "prompt": prompt
        }) as response:
            content = ""
            async for chunk in response.aiter_text():
                chunk = json.loads(chunk)
                content += chunk['response']

    return {"book_name": book_name, "summary": content}

