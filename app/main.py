from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from .database import init_db
from .routers import auth, forms
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize the database
init_db()

app = FastAPI(title="Form Builder API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    session_cookie="session"
)

# Include routers
app.include_router(auth.router)
app.include_router(forms.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Form Builder API"} 