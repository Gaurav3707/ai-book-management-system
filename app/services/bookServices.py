from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from fastapi import HTTPException, Request
from app.models.book import Book, Review
from app.utils.helper import call_ai_model, convert_string_to_json
from app.utils.jwt import fetch_user_by_request
from pydantic import BaseModel
from typing import List

class BookService:
    class BookCreate(BaseModel):
        title: str
        author: str
        genre: str
        year_published: int
        summary: str

    class SummaryCreate(BaseModel):
        content: str

    class ReviewCreate(BaseModel):
        review_text: str
        rating: int

    @staticmethod
    async def create_book(book: BookCreate, db: AsyncSession):
        new_book = Book(**book.model_dump())
        db.add(new_book)
        await db.commit()
        await db.refresh(new_book)
        return new_book

    @staticmethod
    async def list_books(db: AsyncSession):
        result = await db.execute(select(Book))
        return result.scalars().all()

    @staticmethod
    async def get_recommendations(request: Request, db: AsyncSession):
        user = fetch_user_by_request(request)
        result = await db.execute(select(Book).join(Review).where(Review.user_id == user['user_id'], Review.rating >= 4))
        highly_rated_books = result.scalars().all()
        books_for_prompt = ", ".join([f"{book.title} by {book.author}" for book in highly_rated_books]) if highly_rated_books else "none"
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
        </Instruction>"""
        content = await call_ai_model(prompt)
        return await convert_string_to_json(content)

    @staticmethod
    async def get_book(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            return result.scalar_one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")

    @staticmethod
    async def update_book(book_id: int, book: BookCreate, db: AsyncSession):
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
            raise HTTPException(status_code=404, detail="Book not found")

    @staticmethod
    async def delete_book(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            await db.delete(book)
            await db.commit()
            return {"message": "Book deleted successfully"}
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")

    @staticmethod
    async def add_review(book_id: int, review: ReviewCreate, request: Request, db: AsyncSession):
        try:
            await db.execute(select(Book).where(Book.id == book_id))
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
        user = fetch_user_by_request(request)
        review_data = review.model_dump()
        review_data['user_id'] = user['user_id']
        new_review = Review(book_id=book_id, **review_data)
        db.add(new_review)
        await db.commit()
        await db.refresh(new_review)
        return new_review

    @staticmethod
    async def get_reviews(book_id: int, db: AsyncSession):
        result = await db.execute(select(Review).where(Review.book_id == book_id))
        return result.scalars().all()

    @staticmethod
    async def get_book_summary(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
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

    @staticmethod
    async def generate_summary(content: SummaryCreate):
        prompt = f"Provide a short summary for the following - {content.content}."
        return {"summary": await call_ai_model(prompt)}

    @staticmethod
    async def generate_summary_by_book_id(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
        prompt = f"Provide a short summary for book - {book.title} by {book.author}."
        return {"book_id": book_id, "summary": await call_ai_model(prompt)}

    @staticmethod
    async def generate_summary_by_book_name(book_name: str):
        prompt = f"Provide a short summary for book - {book_name}."
        return {"book_name": book_name, "summary": await call_ai_model(prompt)}
