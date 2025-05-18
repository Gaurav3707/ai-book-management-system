from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
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
        if not book.title or not book.author:
            raise HTTPException(status_code=400, detail="Title and author are required fields")
        try:
            new_book = Book(**book.model_dump())
            db.add(new_book)
            await db.commit()
            await db.refresh(new_book)
            return {"data": new_book, "status": 201, "message": "Book created successfully"}
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def list_books(db: AsyncSession):
        try:
            books = await db.execute(select(Book))
            return {"data": books.scalars().all(), "status": 200, "message": "Books retrieved successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def get_recommendations(request: Request, db: AsyncSession):
        try:
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
            recommendations = await convert_string_to_json(content)
            return {"data": recommendations, "status": 200, "message": "Recommendations retrieved successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

    @staticmethod
    async def get_book(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            return {"data": book, "status": 200, "message": "Book retrieved successfully"}
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")

    @staticmethod
    async def update_book(book_id: int, book: BookCreate, db: AsyncSession):
        if not book.title or not book.author:
            raise HTTPException(status_code=400, detail="Title and author are required fields")
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            existing_book = result.scalar_one()
            for key, value in book.model_dump().items():
                setattr(existing_book, key, value)
            db.add(existing_book)
            await db.commit()
            await db.refresh(existing_book)
            return {"data": existing_book, "status": 200, "message": "Book updated successfully"}
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def delete_book(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            await db.delete(book)
            await db.commit()
            return {"data": None, "status": 200, "message": "Book deleted successfully"}
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def add_review(book_id: int, review: ReviewCreate, request: Request, db: AsyncSession):
        if not review.review_text or not (1 <= review.rating <= 5):
            raise HTTPException(status_code=400, detail="Review text is required and rating must be between 1 and 5")
        try:
            await db.execute(select(Book).where(Book.id == book_id))
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        try:
            user = fetch_user_by_request(request)
            review_data = review.model_dump()
            review_data['user_id'] = user['user_id']
            new_review = Review(book_id=book_id, **review_data)
            db.add(new_review)
            await db.commit()
            await db.refresh(new_review)
            return {"data": new_review, "status": 201, "message": "Review added successfully"}
        except SQLAlchemyError as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    @staticmethod
    async def get_reviews(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Review).where(Review.book_id == book_id))
            reviews = result.scalars().all()
            return {"data": reviews, "status": 200, "message": "Reviews retrieved successfully"}
        except SQLAlchemyError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

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
        data = {
            "title": book.title,
            "author": book.author,
            "summary": book.summary,
            "average_rating": avg_rating,
            "total_reviews": len(reviews),
        }
        return {"data": data, "status": 200, "message": "Book summary retrieved successfully"}

    @staticmethod
    async def generate_summary(content: SummaryCreate):
        prompt = f"Provide a short summary for the following - {content.content}."
        summary = await call_ai_model(prompt)
        if summary is None:
            return {"data": {"content": content.content, "summary": summary}, "status": 400, "message": "Something went wrong"}
        return {"data": {"content": content.content, "summary": summary}, "status": 200, "message": "Summary generated successfully"}

    @staticmethod
    async def generate_summary_by_book_id(book_id: int, db: AsyncSession):
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
        except NoResultFound:
            raise HTTPException(status_code=404, detail="Book not found")
        prompt = f"Provide a short summary for book - {book.title} by {book.author}."
        summary = await call_ai_model(prompt)
        if summary is None:
            return {"data":{"book_id": book_id, "summary": summary}, "status": 400, "message": "Something went wrong"}
        return {"data":{"book_id": book_id, "summary": summary}, "status": 200, "message": "Summary generated successfully"}

    @staticmethod
    async def generate_summary_by_book_name(book_name: str):
        prompt = f"Provide a short summary for book - {book_name}."
        summary = await call_ai_model(prompt)
        if summary is None:
            return {"data":{"book_name": book_name, "summary": summary}, "status": 400, "message": "Something went wrong"}
        return {"data":{"book_name": book_name, "summary": summary}, "status": 200, "message": "Summary generated successfully"}
