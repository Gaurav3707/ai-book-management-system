from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.utils.jwt import verify_access_token
from app.api.books import router as book_router
from app.config.database import init_db
from app.api.user import router as auth_router
from contextlib import asynccontextmanager
from app.utils.logger import get_logger
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

http_bearer = HTTPBearer()

logger = get_logger(__name__)

async def global_auth_dependency(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)):
    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="Book Management System",
    description="An API for managing books and reviews.",
    version="1.0.0",
    contact={
        "name": "Support Team",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")


# CORS configuration
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom OpenAPI schema to include Bearer token in Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    security_scheme = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["components"]["securitySchemes"] = security_scheme
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "security" not in method:
                method["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def root(request: Request):
    logger.info("Root endpoint accessed.")
    try:
        return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )
    except Exception as e:
        logger.error(f"Error reading README.html: {e}")
        return {"message": "Error loading the README page"}

app.include_router(book_router, prefix="/api/books", tags=["Books"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
