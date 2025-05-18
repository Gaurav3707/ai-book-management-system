import json
import ast
from app.utils.logger import get_logger
from sqlalchemy.future import select
from app.models.book import Book

logger = get_logger(__name__)

async def convert_string_to_json(response):
    logger.debug("Converting string to JSON.")
    try:
        start_idx = response.index('{') if '{' in response else None
        end_idx = response.rfind('}') if '}' in response else None

        if start_idx is not None and end_idx is not None:
            trimmed = response[start_idx:end_idx + 1]
        elif start_idx is not None:
            trimmed = response[start_idx:]
        elif end_idx is not None:
            trimmed = response[:end_idx + 1]
        else:
            trimmed = response

        trimmed = trimmed.replace("```json", "").replace("```", "")
    except Exception as e:
        logger.error(f"Error while trimming response: {e}")
        trimmed = response

    try:
        result = json.loads(trimmed)
        logger.debug("Successfully converted string to JSON.")
        return result
    except json.JSONDecodeError:
        logger.warning("JSON decoding failed, attempting literal evaluation.")
        try:
            result = ast.literal_eval(trimmed)
            logger.debug("Successfully evaluated string to Python object.")
            return result
        except Exception as e:
            logger.error(f"Error during literal evaluation: {e}")
            return response

async def check_duplicate_book(title: str, author: str, db, exclude_book_id: int = None):
    """
    Check if a book with the same title and author already exists in the database.
    Optionally exclude a specific book ID from the check.
    """
    logger.debug(f"Checking for duplicate book: {title} by {author}")
    try:
        query = select(Book).where(Book.title == title, Book.author == author)
        if exclude_book_id:
            query = query.where(Book.id != exclude_book_id)
        result = await db.execute(query)
        is_duplicate = result.scalar() is not None
        logger.debug(f"Duplicate check result: {is_duplicate}")
        return is_duplicate
    except Exception as e:
        logger.error(f"Error while checking for duplicate book: {e}")
        return False