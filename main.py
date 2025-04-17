from fastapi import FastAPI, Depends
from routers.auth import router as auth_router  # import router from the auth file
from database import SessionLocal
from models import Dummy
from pydantic import BaseModel
from sqlalchemy.orm import Session

app = FastAPI()

app.include_router(auth_router)


class Item(BaseModel):
    name: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/{name}")
async def home(name: str, db: Session = Depends(get_db)):
    db_items = Dummy(name=name)
    db.add(db_items)
    db.commit()
    db.refresh(db_items)
    return db_items
