import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import List
from datetime import datetime
from typing import Annotated
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from dependecies import get_current_user_from_cookie
import models

load_dotenv()


AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

router = APIRouter(
    prefix="/files",
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
    s3_url: str
    content_type: str

    class Config:
        orm_mode = True


class UserFileDetail(BaseModel):
    filename: str
    uploaded_at: datetime
    updated_at: datetime
    s3_url: str
    size: int
    content_type: str


@router.get("/", response_model=List[UserFiles], status_code=status.HTTP_200_OK)
async def get_user_files(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):

    user_files = db.query(models.File).filter(models.File.owner_id == user.id).all()

    return user_files


# TODO: set a max limit for excepting the file
# TODO: directly send the file to the s3 bucket
# TODO: extract the meta data from the file and store it in the postgres


@router.post(
    "/", response_model=List[UserFileDetail], status_code=status.HTTP_201_CREATED
)
async def upload_user_files(
    request: Request,
    files: List[UploadFile],
    db: Session = Depends(get_db),
    user=Depends(get_current_user_from_cookie),
):
    uploaded_files_details = []

    for file in files:

        # build bucket key (user_id/uuid<.ext>)
        # get the file extesion
        file_extension = os.path.splitext(file.filename)[1]

        s3_object_key = f"{user.id}/{uuid.uuid4()}{file_extension}"

        try:
            s3_client.upload_fileobj(
                file.file,  # The file-like object from UploadFile
                S3_BUCKET_NAME,  # Your bucket name
                s3_object_key,  # The unique key (path) in S3
                ExtraArgs={  # Optional: Set metadata like ContentType
                    "ContentType": file.content_type
                },
            )

            # --- 3. Construct the S3 URL (Optional but useful) ---
            # Note: This URL might not be publicly accessible unless bucket/object ACLs allow it,
            # or you generate pre-signed URLs later for access.
            s3_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_object_key}"

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

                db.add(db_file)
                db.commit()
                db.refresh(db_file)

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
                print(f"database upload error {file.filename} as {e}")
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save the metadata of file {file.filename}",
                )

        except ClientError as e:
            print(f"s3 upload eror {file.filename} as {e}")
            raise HTTPException(
                status_code=500, detail=f"failed to upload {file.filename} to S3"
            )

        except Exception as e:
            print(f"failed to process the file {file.filename} as {e}")
            raise HTTPException(
                status_code=400, detail=f"falied to process the file {file.filename}"
            )
        finally:
            await file.close()

    return uploaded_files_details
