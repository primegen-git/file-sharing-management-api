import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import models
from database import get_db
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from logger import logger
from uuid import UUID

router = APIRouter(
    prefix="/auth", tags=["auth"], responses={401: {"message": "unauthorized access"}}
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

ALGORITHM = os.getenv("ALGORITHM")

# PYDANTIC MODE


class UserLogin(BaseModel):
    username: str
    email: str
    password: str


class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# HELPERS FUNCTION


def validate_user_data(user, db):

    # NOTE: first check the password then move forward

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


def authenticate_user(username, password, db):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(
    username: str, user_id: str, expires_delta: Optional[timedelta] = None
):
    # create the payload for the token with "sub", "expire_time"
    # encode it with the jwt method
    to_encode = {"sub": username, "user_id": user_id}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode["exp"] = str(int(expire.timestamp()))
    try:
        if not SECRET_KEY or not ALGORITHM:
            logger.error("SECRET_KEY or ALGORITHM is not set in environment variables.")
            raise HTTPException(
                status_code=500, detail="Token generation misconfiguration."
            )
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"JWT encoding failed: {e}")
        raise HTTPException(status_code=500, detail="Could not generate token.")


@router.get("/")
async def auth():
    return {"mess": "inside the auth"}


# TODO: define different message if pydantic validation failed
@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)  # response_model is used to define the structure of the data returend from the endpoinit with automatic filternation
async def register_user(
    user: UserRegister, db: Session = Depends(get_db)
):  # UserRegister will be used to verify the json response and create a user object after that
    try:
        validate_user_data(user, db)
        user_model = models.User(
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
        )
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
        return user_model
    except HTTPException as e:
        logger.error(f"Registration HTTPException for user {user.username}: {e.detail}")
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            f"Some internal issue occur in registration for user {user.username}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Some internal issue occur in registration {str(e)}",
        )


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
async def loginUser(user: UserLogin, db: Session = Depends(get_db)):
    try:
        auth_user = authenticate_user(user.username, user.password, db)
        if not auth_user:
            logger.warning(
                f"Login failed for username {user.username}: incorrect credentials."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="incorrect username or password",
            )
        access_token_expires = timedelta(minutes=60)
        access_token = create_access_token(
            username=str(auth_user.username),
            user_id=str(auth_user.id),
            expires_delta=access_token_expires,
        )
        response = JSONResponse(content="login successfull")
        response.set_cookie(
            key="access_token", value=access_token, httponly=True, secure=True, path="/"
        )
        logger.info(f"User {user.username} logged in successfully.")
        return response
    except HTTPException as e:
        logger.error(f"Login HTTPException for user {user.username}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Could not generate token for user {user.username}: {e}")
        raise HTTPException(status_code=500, detail=f"could not generate token")


@router.post("/logout")
async def logoutUser():
    try:
        msg = {"message": "Logout successful. We hope to see you again soon!"}
        response = JSONResponse(content=msg)
        response.delete_cookie(key="access_token")
        logger.info("User logged out successfully.")
        return response
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail="Could not logout user.")
