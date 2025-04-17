from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import models
from database import get_db
from sqlalchemy.orm import Session
from passlib.hash import pbkdf2_sha256
from uuid import UUID

router = APIRouter(
    prefix="/auth", tags=["auth"], responses={401: {"message": "unauthorized access"}}
)


class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str


def get_hashed_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_hashed_password(password: str, hashed_password: str) -> bool:
    return pbkdf2_sha256.verify(password, hashed_password)


@router.get("/")
async def auth():
    return {"mess": "inside the auth"}


# TODO: define different message if pydantic validation failed
@router.post(
    "/register", response_model=UserResponse
)  # response_model is used to define the structure of the data returend from the endpoinit with automatic filternation
async def register_user(
    user: UserRegister, db: Session = Depends(get_db)
):  # UserRegister will be used to verify the json response and create a user object after that

    # NOTE:  verify the password first before doing the other validation which require the database query

    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="password does not match")

    # check if the username exist in the database or not

    validation1 = (
        db.query(models.User).filter(models.User.username == user.username).first()
    )

    # check if the email already exist in the table or not

    validation2 = db.query(models.User).filter(models.User.email == user.email).first()

    if validation1 is not None:
        raise HTTPException(status_code=400, detail="username already exist")

    if validation2 is not None:
        raise HTTPException(status_code=400, detail="email already exist")

    try:
        user_model = models.User(
            username=user.username,
            email=user.email,
            hashed_password=get_hashed_password(user.password),
        )

        db.add(user_model)
        db.commit()
        db.refresh(user_model)

        return user_model
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Some internal issue occur in registration {str(e)}",
        )
