from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import engine, Base
from routers import users

# --- App Setup ---
app = FastAPI()

# --- Database Setup ---
# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# --- Static Files Setup ---
# Get the absolute path to the static directory
static_dir = os.path.join(os.path.dirname(__file__), 'static')

# Mount the static directory to serve files under /static path
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# --- API Routers ---
# Include the user registration router
app.include_router(users.router)

# --- Root Endpoint ---
@app.get("/")
async def read_index():
    """
    Serves the main index.html file from the static directory.
    """
    index_path = os.path.join(static_dir, 'index.html')
    return FileResponse(index_path)

# To run the app:
# uvicorn main:app --reload