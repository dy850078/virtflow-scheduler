from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.core.worker import lifespan
from app.core.task_db import init_db
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize the database 
init_db()

# Create the FastAPI app with lifespan context manager
app = FastAPI(lifespan=lifespan)

# Include the API router
app.include_router(api_router)

