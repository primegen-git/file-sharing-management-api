from dotenv import load_dotenv

import os
import redis
from fastapi import FastAPI, Depends
from routers.auth import router as auth_router  # import router from the auth file
from routers.user import router as files_router
from database import SessionLocal
from models import Dummy, Base
from pydantic import BaseModel
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from logger import logger

from database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


app.include_router(auth_router)

app.include_router(files_router)


class Item(BaseModel):
    name: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


load_dotenv()

REDIS_HOST_NAME = os.getenv("REDIS_HOST_NAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")


@app.get("/check-redis")
async def check_redis():
    if not REDIS_HOST_NAME or not REDIS_PORT or not REDIS_PASSWORD:
        logger.error(
            "REDIS_USER, REDIS_PORT, or REDIS_PASSWORD environment variable is missing."
        )
        return {
            "error": "REDIS_USER, REDIS_PORT, or REDIS_PASSWORD environment variable is missing."
        }
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST_NAME,
            port=int(REDIS_PORT),
            password=REDIS_PASSWORD,
            decode_responses=True,
        )
        redis_client.set("test-value", "checked passed")
        checked_status = redis_client.get("test-value")
        logger.info("Redis connection and set/get test passed.")
        return {"status": checked_status if checked_status else None}
    except Exception as e:
        logger.error(f"Redis checked failed: {str(e)}")
        return {"error": f"redis checked failed, {str(e)}"}


@app.post("/{name}")
async def home(name: str, db: Session = Depends(get_db)):
    db_items = Dummy(name=name)
    db.add(db_items)
    db.commit()
    db.refresh(db_items)
    return db_items
