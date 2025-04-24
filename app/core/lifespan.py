from contextlib import asynccontextmanager
from app.core.task_db import init_db

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield