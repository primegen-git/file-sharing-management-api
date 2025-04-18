from fastapi import Request, HTTPException, status
import os
import jwt
import models
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def get_current_user_from_cookie(request: Request, db):

    # use the try and except block..

    # STEPS: get the token -> deocode the token -> get the user data -> fetch the user from the database -> return the user. (just handle the potentials errors)
    credential_exceptions = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        token = request.cookies.get("access_token")
        if not token:
            raise credential_exceptions

        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        username = payload.get("sub")

        user = db.query(models.User).filter(models.User.username == username).first()

        if not user:
            raise credential_exceptions

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is Expired",
        )
    except jwt.jwt.InvalidTokenError:
        raise credential_exceptions
