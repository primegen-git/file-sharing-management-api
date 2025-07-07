from fastapi import Request, HTTPException, status, Depends
import os
import jwt
import boto3
import logging
from sqlalchemy.orm import Session
from database import get_db
import models
from dotenv import load_dotenv


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Configure logging
logger = logging.getLogger(__name__)


# Initialize your S3 client
s3_client = boto3.client("s3", region_name=AWS_REGION)


def delete_s3_object(s3_key):
    """
    Deletes the corresponding S3 object after the File record is deleted from the database.
    """
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        logger.info(f"Deleted S3 object: {s3_key}")
    except Exception as e:
        logger.error(f"Failed to delete S3 object {s3_key}: {e}")


def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):

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
    except jwt.InvalidTokenError:
        raise credential_exceptions
