# Book Management System

The Book Management System is a FastAPI-based application that allows users to manage books and their reviews. It includes features like adding, updating, deleting books, managing reviews, and generating summaries using an external AI model. The application leverages a locally running Ollama instance to generate book summaries and provide book recommendations.

## Features

- Add, update, delete books.
- Manage reviews for books.
- Generate summaries for books using a locally running Ollama instance.
- Fetch book recommendations using Ollama.
- Detailed logging for all operations to track application flow and errors.**

## Project Structure

- `app/`: Contains the main application code.
  - `api/`: API routes for books and user authentication.
    - `books.py`: Handles book-related operations.
    - `users.py`: Handles user authentication.
  - `config/`: Configuration settings for the application.
    - `database.py`: Database connection settings.
    - `settings.py`: Stores application settings.
  - `models/`: Database models.
    - `book.py`: Book model.
    - `user.py`: User model.
  - `services.py`: Service layer for business logic.
    - `bookServices.py`: Book-related business logic.
    - `userServices.py`: User-related business logic.
  - `utils/`: Utility functions and dependencies.
    - `messages`: Response messages for API endpoints.
    - `ai_inference.py`: Functions for interacting with the Ollama instance and Open Router.
    - `auth.py`: Functions for user authentication.
    - `decorators.py`: Decorators for API routes.
    - `dependencies.py`: Dependency injection for API routes.
    - `helper.py`: Helper functions for API routes.
    - `jwt.py`: Functions for JWT token generation and verification.
    - `logger.py`: Functions for logging.
- `docker`: Docker configuration for the application.
- `migrations/`: Database migration files.
- `model`: Ollama model is stored.
- `templates`: HTML templates for the application.
- `tests/`: Test suites for API endpoints.
- `.env`: Environment variables for sensitive data.
- `main.py`: Entry point for the application.
- `README.md`: This file.
- `requirements.txt`: Dependencies for the application.


## Prerequisites

- Python 3.9+
- PostgreSQL database
- `pip` for managing Python packages
- Ollama installed and running locally

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd book-management-system
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
   AI_MODEL=llama3.2:1b
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

### User Authentication

- **Register User**  
  `POST /auth/register`  
  Request Body:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```

- **Login User**  
  `POST /auth/login`  
  Request Body:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
  Response:
  ```json
  {
    "access_token": "string",
    "token_type": "bearer"
  }
  ```

- **Get User Profile**  
  `GET /auth/profile`  
  Headers: `Authorization: Bearer <access_token>`  
  Response:
  ```json
  {
    "username": "string",
    "role": "string"
  }
  ```

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
  Headers: `Authorization: Bearer <access_token>`

- **Get a Book by ID**  
  `GET /api/books/{book_id}`  
  Headers: `Authorization: Bearer <access_token>`

- **Update a Book**  
  `PUT /api/books/{book_id}`  
  Request Body: Same as "Create a Book".  
  Headers: `Authorization: Bearer <access_token>`

- **Delete a Book**  
  `DELETE /api/books/{book_id}`  
  Headers: `Authorization: Bearer <access_token>`

### Reviews

- **Add a Review**  
  `POST /api/books/{book_id}/reviews`  
  Request Body:
  ```json
  {
    "review_text": "Great book!",
    "rating": 5
  }
  ```
  Headers: `Authorization: Bearer <access_token>`

- **List Reviews for a Book**  
  `GET /api/books/{book_id}/reviews`  
   Headers: `Authorization: Bearer <access_token>`

### Summaries

- **Generate Summary for Custom Content**  
  `POST /api/books/generate-summary`  
  Request Body:
  ```json
  {
    "content": "Custom content to summarize."
  }
  ```
   Headers: `Authorization: Bearer <access_token>`

- **Generate Summary for a Book by ID**  
  `POST /api/books/generate-summary-by-book-id/{book_id}`  
   Headers: `Authorization: Bearer <access_token>`

- **Generate Summary for a Book by Name**  
 `GET /api/books/generate-summary-by-book-name/{book_name}`
   Headers: `Authorization: Bearer <access_token>`

- **Get Book Summary**  
  `GET /api/books/{book_id}/summary`  
   Headers: `Authorization: Bearer <access_token>`

### Recommendations
- **Get Book Recommendations**  
  `GET /api/books/recommendations`
   Headers: `Authorization: Bearer <access_token>`

## Environment Variables

- `DATABASE_URL`: Connection string for the PostgreSQL database.
- `JWT_SECRET`: Secret key for JWT authentication.
- `JWT_ALGORITHM`: Algorithm used for JWT.
- `OLLAMA_ENDPOINT`: Endpoint for the AI model to generate summaries and recommendations.
- `AI_MODEL`: The name of the AI model pulled on Ollama.

## Logging

The application includes detailed logging for all operations. Logs are categorized as:

- **INFO**: For successful operations like creating, updating, or deleting books.
- **WARNING**: For invalid inputs or missing data.
- **ERROR**: For database errors or unexpected issues.

Logs help in debugging and tracking the flow of the application.

## Testing

The application includes a comprehensive test suite using `pytest` and `pytest-asyncio`. Tests cover:

- User authentication (registration, login, profile access).
- Book management (creation, retrieval, update, deletion).
- Review management (adding and listing reviews).
- Summary generation.
- Book recommendations.

To run the tests:

```bash
pytest
```

Ensure that the test database is properly configured and that all necessary environment variables are set before running the tests.