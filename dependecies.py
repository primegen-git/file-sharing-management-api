from fastapi import Request
import os
import jwt
import models
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


def get_current_user_from_cookie(request: Request, db):

    # get the token from the cookie
    # check if token is present
    # decode the token
    # get the username
    # query the user from the database

    token = request.cookies.get("access_token")

    if not token:
        return None
    payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
    username = payload.get("sub")

    user = db.query(models.User).filter(models.User.username == username).first()

    return user
