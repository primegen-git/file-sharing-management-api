import hashlib
import io
import os
import redis
import boto3
import json
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import List
from datetime import datetime
from uuid import UUID
import uuid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
    UploadFile,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator, ValidationInfo
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from database import get_db
from dependecies import get_current_user_from_cookie, delete_s3_object
import models
from logger import logger

load_dotenv()


AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REDIS_HOST_NAME = os.getenv("REDIS_HOST_NAME")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

router = APIRouter(
    prefix="/user",
    tags=["files"],
    dependencies=[Depends(get_current_user_from_cookie)],
)

s3_client = boto3.client("s3", region_name=AWS_REGION)


class UserFiles(BaseModel):
    id: UUID
    filename: str
    uploaded_at: datetime
    updated_at: datetime
    size: int
    access_url: str
    content_type: str

    class Config:
        from_attributes = True


class UserFileDetail(BaseModel):
    filename: str | None
    uploaded_at: datetime
    updated_at: datetime
    s3_url: str
    size: int | None
    content_type: str | None

    class config:
        validate_assignment = True

    """
     assign predefined value to attributes if None is provided
     available with pydantic(V2)
    """

    @field_validator("filename", "size", "content_type", mode="before")
    @classmethod
    def none_to_default(cls, v, info: ValidationInfo):
        if v is None:
            if info.field_name == "filename":
                return "untitiled"
            if info.field_name == "size":
                return 0
            if info.field_name == "content_type":
                return "application/octet_stream"
        return v


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """

    Args:
        bucket_name (): Name of the s3_bucket.
        object_name (): s3_object_key.
        expiration (): time till the link will be valid.

    Returns:
        public access url for s3_object


    """
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        return None
    return response


def authenticate_redis():
    if REDIS_HOST_NAME is None:
        raise RuntimeError("HOST_NAME is not set in env")
    if REDIS_PORT is None:
        raise RuntimeError("PORT_NUMBER is not set in env")
    if REDIS_PASSWORD is None:
        raise RuntimeError("REDIS_PASSWORD is not set in env")

    # print(REDIS_PASSWORD)

    try:
        r = redis.Redis(
            host=REDIS_HOST_NAME, port=int(REDIS_PORT), password=REDIS_PASSWORD
        )
        return r
    except Exception as e:
        raise


def get_redis_key(base, filter_param):
    """

    Args:
        base (): user_id
        filter_param (): user_search_query | all

    Returns:
        return a custom key for the redis key-value pair so that i can differentiate between the all query or the search query

    """
    key = None
    if filter_param:
        if filter_param == "all":
            key = f"{str(base)}:all"
        else:
            hashed_key = hashlib.md5(filter_param.encode()).hexdigest()
            key = f"{str(base)}:filter:{hashed_key}"
    return key


def get_redis(base, filter_param):
    """

    Args:
        base (): user.id
        filter_param (): either "all" or JSON string json.dumps()

    Returns:
        return the data for key from redis

    """
    r = authenticate_redis()

    key = get_redis_key(base, filter_param)

    if key:
        if r.exists(key):
            data = r.get(key)
            if isinstance(data, bytes):
                list_of_files = json.loads(data.decode("utf-8"))
            elif isinstance(data, str):
                list_of_files = json.loads(data)
            else:
                list_of_files = None

            if list_of_files is not None:
                return list_of_files

    return None


def set_redis(base, filter_param, data):

    r = authenticate_redis()

    key = get_redis_key(base, filter_param)
    if key:
        try:
            r.set(key, json.dumps(data), ex=5 * 60)  # expire in 5 minutes
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error in storing value in redis {str(e)}"
            )


def delete_redis(base):
    r = authenticate_redis()

    pattern = f"{str(base)}:*"
    for key in r.scan_iter(pattern):
        r.delete(key)


def search_files(
    db: Session,
    user: models.User,
    filename: str | None = None,
    file_extension: str | None = None,
    content_type: str | None = None,
) -> list:

    response_files = []

    try:
        filters = [models.File.owner_id == user.id]

        if filename:
            filters.append(models.File.filename.ilike("%{filename}%"))
        if file_extension:
            filters.append(models.File.file_extension == file_extension)
        if content_type:
            filters.append(models.File.content_type == content_type)
        try:
            stmt = select(models.File).where(*filters)
            result = db.execute(stmt)
            user_files = result.scalars().all()
            response_files = []
            for file in user_files:
                access_url = create_presigned_url(
                    S3_BUCKET_NAME, file.storage_path, expiration=3600
                )

                file_data = {
                    "id": str(file.id),
                    "filename": file.filename,
                    "uploaded_at": str(file.uploaded_at),
                    "updated_at": str(file.updated_at),
                    "size": file.size,
                    "access_url": access_url,
                    "content_type": file.content_type,
                }
                response_files.append(file_data)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in fetching files from database. {str(e)}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in getting the files. {str(e)}"
        )

    return response_files


def get_filter_param(
    filename: str | None = None,
    file_extension: str | None = None,
    content_type: str | None = None,
):

    filter_param = None

    if not filename and not content_type and not file_extension:
        filter_param = "all"
    else:
        query_param = {
            "filename": filename,
            "content_type": content_type,
            "file_extension": file_extension,
        }
        filter_param = json.dumps(query_param)

    return filter_param


def upload_to_s3(file_bytes, content_type, s3_object_key: str, filename):
    try:
        s3_client.upload_fileobj(
            io.BytesIO(file_bytes),  # The file-like object from UploadFile
            S3_BUCKET_NAME,  # Your bucket name
            s3_object_key,  # The unique key (path) in S3
            ExtraArgs={  # Optional: Set metadata like ContentType
                "ContentType": content_type
            },
        )
    except ClientError as e:
        logger.error(f"s3 upload error {filename}: {e}")
        raise HTTPException(
            status_code=500, detail=f"failed to upload {filename} to S3"
        )
    except Exception as e:
        logger.error(f"failed to process the file {filename}: {e}")
        raise HTTPException(
            status_code=400, detail=f"failed to process the file {filename}"
        )


@router.get("/check-redis")
async def check_redis(request: Request):
    try:
        logger.info("inside-parameter-function")
        r = authenticate_redis()
        logger.info(f"Redis instance: {r}")
        r.set("test", "test-successfull")
        return {r.get("test")}
    except Exception as e:
        logger.error(f"Error in /check-redis: {e}")
        raise HTTPException(status_code=500, detail="Error in check-redis endpoint.")


@router.get("/files", response_model=List[UserFiles], status_code=status.HTTP_200_OK)
async def get_files(
    request: Request,
    filename: str | None = None,
    content_type: str | None = None,
    file_extension: str | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):

    filter_param = get_filter_param(filename, file_extension, content_type)

    if not get_redis(user.id, filter_param):
        response_files = search_files(db, user, filename, file_extension, content_type)
        if response_files:
            set_redis(user.id, filter_param, response_files)
        return response_files

    else:
        list_of_files = get_redis(user.id, filter_param)
        return list_of_files


@router.delete("/files", status_code=status.HTTP_200_OK)
async def delete_files(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):
    try:
        user_files = db.scalars(
            select(models.File).where(models.File.owner_id == user.id)
        ).all()

        db.execute(delete(models.File).where(models.File.owner_id == user.id))
        db.commit()

        delete_redis(user.id)

        for file in user_files:
            background_tasks.add_task(delete_s3_object, file.storage_path)

        msg = {"message": "All your files have been deleted successfully."}
        return JSONResponse(content=msg)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"fail to delete files {str(e)}")


# TODO: set a max limit for excepting the file


@router.post(
    "/upload", response_model=List[UserFileDetail], status_code=status.HTTP_201_CREATED
)
async def upload_user_files(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile],  # NOTE: key : files, value = actual file
    db: Session = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    uploaded_files_details = []
    for file in files:

        # build bucket key (user_id/uuid<.ext>)
        # get the file extension
        file_extension = ""
        if file.filename:
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ""

        s3_object_key = f"{user.id}/{uuid.uuid4()}{file_extension}"

        file_bytes = (
            await file.read()
        )  # read the file before you add to the background task
        background_tasks.add_task(
            upload_to_s3, file_bytes, file.content_type, s3_object_key, file.filename
        )

        # --- 3. Construct the S3 URL (Optional but useful) ---
        # Note: This URL might not be publicly accessible unless bucket/object ACLs allow it,
        # or you generate pre-signed URLs later for access.
        s3_url = (
            f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_object_key}"
        )

        try:
            db_file = models.File(
                filename=file.filename,
                size=file.size,
                storage_path=s3_object_key,
                s3_url=s3_url,
                content_type=file.content_type,
                owner_id=user.id,
                owner=user,
            )

            if file_extension:
                db_file.file_extension = file_extension

            db.add(db_file)
            db.commit()
            db.refresh(db_file)
            user_files = search_files(db, user)
            filter_param = get_filter_param()
            set_redis(user.id, filter_param, user_files)

            # TODO: add a method to update the redis instance todo-2
            delete_redis(user.id)

            response_object = UserFileDetail(
                filename=file.filename,
                uploaded_at=db_file.uploaded_at,
                updated_at=db_file.updated_at,
                size=file.size,
                s3_url=s3_url,
                content_type=file.content_type,
            )
            uploaded_files_details.append(response_object)

        except Exception as e:
            logger.error(f"database upload error {file.filename}: {e}")
            db.rollback()
            try:
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, key=s3_object_key)
            except Exception as delete_error:
                logger.error(f"failed to delete orphaned s3 file: {delete_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save the metadata of file {file.filename}",
            )

    return uploaded_files_details


@router.delete("/")
async def deleteUser(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):
    try:
        user_id = user.id
        db.delete(user)
        db.commit()

        delete_redis(user_id)

        # NOTE: now delete the access token also
        msg = {
            "message": "Your account and all files have been deleted successfully. We're sorry to see you go!"
        }
        response = JSONResponse(content=msg)
        response.delete_cookie(key="access_token")
        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"failed to delete the user instance {str(e)}"
        )
