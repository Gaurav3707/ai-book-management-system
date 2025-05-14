# Book Management System

The Book Management System is a FastAPI-based application that allows users to manage books and their reviews. It includes features like adding, updating, deleting books, managing reviews, and generating summaries using an external AI model. The application leverages a locally running Ollama instance to generate book summaries and provide book recommendations.

## Features

- Add, update, delete books.
- Manage reviews for books.
- Generate summaries for books using a locally running Ollama instance.
- Fetch book recommendations using Ollama.

## Project Structure

- `app/`: Contains the main application code.
  - `api/`: API routes for books and reviews.
  - `config/`: Configuration settings for the application.
  - `models/`: Database models.
- `migrations/`: Database migration files.
- `.env`: Environment variables for sensitive data.

## Prerequisites

- Python 3.9+
- PostgreSQL database
- `pip` for managing Python packages

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd book-management-system/book_management
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add the following:
   ```dotenv
   DATABASE_URL=postgresql+asyncpg://<username>:<password>@<host>/<database>
   JWT_SECRET=your_jwt_secret
   JWT_ALGORITHM=HS256
   OLLAMA_ENDPOINT=http://localhost:11434/api/generate
   ```

5. Apply database migrations:
   ```bash
   alembic upgrade head
   ```

6. Download and run the AI model using Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama run llama3.2:1b
   ```

7. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

8. Access the API documentation at:
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### Books

- **Create a Book**  
  `POST /api/books/`  
  Request Body:
  ```json
  {
    "title": "Book Title",
    "author": "Author Name",
    "genre": "Genre",
    "year_published": 2023,
    "summary": "Book summary."
  }
  ```

- **List All Books**  
  `GET /api/books/`

- **Get a Book by ID**  
  `GET /api/books/{book_id}`

- **Update a Book**  
  `PUT /api/books/{book_id}`  
  Request Body: Same as "Create a Book".

- **Delete a Book**  
  `DELETE /api/books/{book_id}`

### Reviews

- **Add a Review**  
  `POST /api/books/{book_id}/reviews`  
  Request Body:
  ```json
  {
    "user_id": 1,
    "review_text": "Great book!",
    "rating": 5
  }
  ```

- **List Reviews for a Book**  
  `GET /api/books/{book_id}/reviews`

### Summaries

- **Generate Summary for a Book**  
  `POST /api/books/generate-summary/{book_id}`

- **Generate Summary for Custom Content**  
  `POST /api/books/generate-summary`  
  Request Body:
  ```json
  {
    "content": "Custom content to summarize."
  }
  ```

### Recommendations

- **Get Book Recommendations**  
  `GET /api/books/recommendations`

## Environment Variables

- `DATABASE_URL`: Connection string for the PostgreSQL database.
- `JWT_SECRET`: Secret key for JWT authentication.
- `JWT_ALGORITHM`: Algorithm used for JWT.
- `OLLAMA_ENDPOINT`: Endpoint for the AI model to generate summaries and recommendations.
- `AI_MODEL`: Pulled AI model on ollama.