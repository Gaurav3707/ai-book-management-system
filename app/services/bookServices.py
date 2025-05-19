from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from fastapi import HTTPException, Request
from app.models.book import Book, Review
from app.utils.helper import convert_string_to_json, check_duplicate_book
from app.utils.ai_inference import InferenceHelper
from app.utils.jwt import fetch_user_by_request
from pydantic import BaseModel
from app.utils.messages.bookMessages import (
    BOOK_CREATED_SUCCESS, BOOK_RETRIEVED_SUCCESS, BOOK_UPDATED_SUCCESS,
    BOOK_DELETED_SUCCESS, BOOK_NOT_FOUND, BOOKS_RETRIEVED_SUCCESS,
    RECOMMENDATIONS_RETRIEVED_SUCCESS, REVIEWS_RETRIEVED_SUCCESS,
    REVIEW_ADDED_SUCCESS, BOOK_SUMMARY_RETRIEVED_SUCCESS,
    SUMMARY_GENERATED_SUCCESS, SUMMARY_GENERATION_FAILED,
    INVALID_REVIEW_INPUT, INVALID_BOOK_INPUT, DATABASE_ERROR, 
    DUPLICATE_BOOK, DUPLICATE_REVIEW, NO_AI_CONTENT
)
from app.utils.logger import get_logger
from app.utils.instructions import LLMInstructions

logger = get_logger(__name__)

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
        logger.info(f"Creating book: {book.title}")
        if not book.title or not book.author:
            logger.warning("Invalid book input: Missing title or author.")
            return {"data": None, "status": 400, "message": INVALID_BOOK_INPUT}
        try:
            # Check for duplicate book title and author
            if await check_duplicate_book(book.title, book.author, db):
                logger.warning(f"Duplicate book found: {book.title} by {book.author}")
                return {"data": None, "status": 400, "message": DUPLICATE_BOOK}
            
            new_book = Book(**book.model_dump())
            db.add(new_book)
            await db.commit()
            await db.refresh(new_book)
            logger.info(f"Book created successfully: {new_book}")
            return {"data": new_book, "status": 201, "message": BOOK_CREATED_SUCCESS}
        except SQLAlchemyError as e:
            logger.error(f"Database error while creating book: {str(e)}")
            await db.rollback()
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}

    @staticmethod
    async def list_books(db: AsyncSession):
        logger.info("Fetching list of books.")
        try:
            result = await db.execute(select(Book))
            books = result.scalars().all()
            logger.info(f"Books retrieved successfully: {len(books)} books found.")
            logger.debug(f"Books data: {books}")
            return {"data": books, "status": 200, "message": BOOKS_RETRIEVED_SUCCESS}
        except SQLAlchemyError as e:
            logger.error(f"Database error while listing books: {str(e)}")
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}

    @staticmethod
    async def get_recommendations(request: Request, db: AsyncSession):
        logger.info("Generating book recommendations.")
        try:
            user = fetch_user_by_request(request)
            logger.debug(f"User fetched from request: {user}")
            result = await db.execute(select(Book).join(Review).where(Review.user_id == user['user_id'], Review.rating >= 4))
            highly_rated_books = result.scalars().all()
            logger.debug(f"Highly rated books by user: {highly_rated_books}")
            books_for_prompt = ", ".join([f"{book.title} by {book.author}" for book in highly_rated_books]) if highly_rated_books else "none"
            prompt = LLMInstructions.get_recommendation_prompt(books_for_prompt)
            content = await InferenceHelper.call_ai_model(prompt)
            if content is None:
                logger.warning("AI model returned no content.")
                return {"data": None, "status": 400, "message": NO_AI_CONTENT}
            logger.debug(f"AI model response: {content}")
            recommendations = await convert_string_to_json(content)
            logger.info("Recommendations generated successfully.")
            return {"data": recommendations, "status": 200, "message": RECOMMENDATIONS_RETRIEVED_SUCCESS}
        except SQLAlchemyError as e:
            logger.error(f"Database error while generating recommendations: {str(e)}")
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return {"data": None, "status": 500, "message": f"Error generating recommendations: {str(e)}"}

    @staticmethod
    async def get_book(book_id: int, db: AsyncSession):
        logger.info(f"Fetching book with ID: {book_id}")
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            logger.info(f"Book retrieved successfully: {book}")
            return {"data": book, "status": 200, "message": BOOK_RETRIEVED_SUCCESS}
        except NoResultFound:
            logger.warning(f"Book not found with ID: {book_id}")
            return {"data": None, "status": 404, "message": BOOK_NOT_FOUND}

    @staticmethod
    async def update_book(book_id: int, book: BookCreate, db: AsyncSession):
        logger.info(f"Updating book with ID: {book_id}")
        if not book.title or not book.author:
            logger.warning("Invalid book input: Missing title or author.")
            return {"data": None, "status": 400, "message": INVALID_BOOK_INPUT}
        try:
            # Check for duplicate book title and author
            if await check_duplicate_book(book.title, book.author, db, exclude_book_id=book_id):
                logger.warning(f"Duplicate book found: {book.title} by {book.author}")
                return {"data": None, "status": 400, "message": DUPLICATE_BOOK}
            
            result = await db.execute(select(Book).where(Book.id == book_id))
            existing_book = result.scalar_one()
            logger.debug(f"Existing book data: {existing_book}")
            for key, value in book.model_dump().items():
                setattr(existing_book, key, value)
            db.add(existing_book)
            await db.commit()
            await db.refresh(existing_book)
            logger.info(f"Book updated successfully: {existing_book}")
            return {"data": existing_book, "status": 200, "message": BOOK_UPDATED_SUCCESS}
        except NoResultFound:
            logger.warning(f"Book not found with ID: {book_id}")
            return {"data": None, "status": 404, "message": BOOK_NOT_FOUND}
        except SQLAlchemyError as e:
            logger.error(f"Database error while updating book: {str(e)}")
            await db.rollback()
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}

    @staticmethod
    async def delete_book(book_id: int, db: AsyncSession):
        logger.info(f"Deleting book with ID: {book_id}")
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            logger.debug(f"Book to be deleted: {book}")
            await db.delete(book)
            await db.commit()
            logger.info(f"Book deleted successfully with ID: {book_id}")
            return {"data": None, "status": 200, "message": BOOK_DELETED_SUCCESS}
        except NoResultFound:
            logger.warning(f"Book not found with ID: {book_id}")
            return {"data": None, "status": 404, "message": BOOK_NOT_FOUND}
        except SQLAlchemyError as e:
            logger.error(f"Database error while deleting book: {str(e)}")
            await db.rollback()
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}

    @staticmethod
    async def add_review(book_id: int, review: ReviewCreate, request: Request, db: AsyncSession):
        logger.info(f"Adding review for book ID: {book_id}")
        if not review.review_text or not (1 <= review.rating <= 5):
            logger.warning("Invalid review input: Missing review text or rating out of range.")
            return {"data": None, "status": 400, "message": INVALID_REVIEW_INPUT}
        try:
            await db.execute(select(Book).where(Book.id == book_id))
        except NoResultFound:
            logger.warning(f"Book not found with ID: {book_id}")
            return {"data": None, "status": 404, "message": BOOK_NOT_FOUND}
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching book for review: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        try:
            user = fetch_user_by_request(request)
            logger.debug(f"User fetched from request: {user}")
            
            # Check if the user has already reviewed this book
            existing_review = await db.execute(
                select(Review).where(Review.book_id == book_id, Review.user_id == user['user_id'])
            )
            if existing_review.scalar():
                logger.warning(f"User {user['user_id']} has already reviewed book ID: {book_id}")
                return {"data": None, "status": 400, "message": DUPLICATE_REVIEW}
            
            review_data = review.model_dump()
            review_data['user_id'] = user['user_id']
            new_review = Review(book_id=book_id, **review_data)
            db.add(new_review)
            await db.commit()
            await db.refresh(new_review)
            logger.info(f"Review added successfully: {new_review}")
            return {"data": new_review, "status": 201, "message": REVIEW_ADDED_SUCCESS}
        except SQLAlchemyError as e:
            logger.error(f"Database error while adding review: {str(e)}")
            await db.rollback()
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}

    @staticmethod
    async def get_reviews(book_id: int, db: AsyncSession):
        logger.info(f"Fetching reviews for book ID: {book_id}")
        try:
            result = await db.execute(select(Review).where(Review.book_id == book_id))
            reviews = result.scalars().all()
            logger.info(f"Reviews retrieved successfully: {len(reviews)} reviews found.")
            return {"data": reviews, "status": 200, "message": REVIEWS_RETRIEVED_SUCCESS}
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching reviews: {str(e)}")
            return {"data": None, "status": 500, "message": f"{DATABASE_ERROR}: {str(e)}"}

    @staticmethod
    async def get_book_summary(book_id: int, db: AsyncSession):
        logger.info(f"Fetching summary for book ID: {book_id}")
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            logger.info(f"Book retrieved successfully: {book}")
        except NoResultFound:
            logger.warning(f"Book not found with ID: {book_id}")
            return {"data": None, "status": 404, "message": BOOK_NOT_FOUND}
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
        logger.info(f"Summary retrieved successfully for book ID: {book_id}")
        return {"data": data, "status": 200, "message": BOOK_SUMMARY_RETRIEVED_SUCCESS}

    @staticmethod
    async def generate_summary(content: SummaryCreate):
        logger.info("Generating summary for provided content.")
        prompt = LLMInstructions.get_content_summary_prompt(content.content)
        summary = await InferenceHelper.call_ai_model(prompt)
        if summary is None:
            logger.warning(SUMMARY_GENERATION_FAILED)
            return {"data": {"content": content.content, "summary": summary}, "status": 400, "message": SUMMARY_GENERATION_FAILED}
        logger.info(SUMMARY_GENERATED_SUCCESS)
        return {"data": {"content": content.content, "summary": summary}, "status": 200, "message": SUMMARY_GENERATED_SUCCESS}

    @staticmethod
    async def generate_summary_by_book_id(book_id: int, db: AsyncSession):
        logger.info(f"Generating summary for book ID: {book_id}")
        try:
            result = await db.execute(select(Book).where(Book.id == book_id))
            book = result.scalar_one()
            logger.info(f"Book retrieved successfully: {book}")
        except NoResultFound:
            logger.warning(f"Book not found with ID: {book_id}")
            raise HTTPException(status_code=404, detail="Book not found")
        prompt = LLMInstructions.get_summary_book_id_prompt(book.title, book.author)
        summary = await InferenceHelper.call_ai_model(prompt)
        if summary is None:
            logger.warning(SUMMARY_GENERATION_FAILED)
            return {"data":{"book_id": book_id, "summary": summary}, "status": 400, "message": SUMMARY_GENERATION_FAILED}
        logger.info(SUMMARY_GENERATED_SUCCESS)
        return {"data":{"book_id": book_id, "summary": summary}, "status": 200, "message": SUMMARY_GENERATED_SUCCESS}

    @staticmethod
    async def generate_summary_by_book_name(book_name: str):
        logger.info(f"Generating summary for book name: {book_name}")
        prompt = LLMInstructions.get_summary_book_name_prompt(book_name)
        summary = await InferenceHelper.call_ai_model(prompt)
        if summary is None:
            logger.warning(SUMMARY_GENERATION_FAILED)
            return {"data":{"book_name": book_name, "summary": summary}, "status": 400, "message": SUMMARY_GENERATION_FAILED}
        logger.info(SUMMARY_GENERATED_SUCCESS)
        return {"data":{"book_name": book_name, "summary": summary}, "status": 200, "message": SUMMARY_GENERATED_SUCCESS}
