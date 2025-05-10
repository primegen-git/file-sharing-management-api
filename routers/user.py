import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from typing import List
from datetime import datetime
from uuid import UUID
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from database import get_db
from dependecies import get_current_user_from_cookie
import models

load_dotenv()


AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

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
        orm_mode = True


class UserFileDetail(BaseModel):
    filename: str
    uploaded_at: datetime
    updated_at: datetime
    s3_url: str
    size: int
    content_type: str


# FUNCTION
def get_full_extension(filename: str) -> str | None:
    if "." not in filename.strip("."):
        return None  # No extension
    parts = filename.split(".")
    return (
        ".".join(parts[1:])
        if not filename.startswith(".")
        else ".".join(parts[2:]) or None
    )


def create_presigned_url(bucket_name, object_name, expiration=3600):
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except Exception as e:
        print(e)
        return None
    return response


# url = create_presigned_url("your-bucket-name", "your-object-key", expiration=3600)


@router.get("/files", response_model=List[UserFiles], status_code=status.HTTP_200_OK)
async def get_files(
    request: Request,
    filename: str | None = None,
    content_type: str | None = None,
    file_extension: str | None = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):

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
                    "id": file.id,
                    "filename": file.filename,
                    "uploaded_at": file.uploaded_at,
                    "updated_at": file.updated_at,
                    "size": file.size,
                    "access_url": access_url,
                    "content_type": file.content_type,
                }
                response_files.append(file_data)
            return response_files
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in fetching files from database. {str(e)}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in getting the files. {str(e)}"
        )


@router.delete("/files", status_code=status.HTTP_200_OK)
async def delete_files(
    request: Request,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):
    try:
        db.execute(delete(models.File).where(models.File.owner_id == user.id))
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"fail to delete files {str(e)}")


# TODO: set a max limit for excepting the file


@router.post(
    "/upload", response_model=List[UserFileDetail], status_code=status.HTTP_201_CREATED
)
async def upload_user_files(
    request: Request,
    files: List[UploadFile],  # key : files, value = actual file
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
                    file_extension=get_full_extension(file.filename),
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

                try:
                    s3_client.delete_object(Bucket=S3_BUCKET_NAME, key=s3_object_key)
                except Exception as delete_error:
                    print(f"failed to delete orphaned s3 file {delete_error}")

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


@router.delete("/")
async def deleteUser(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user_from_cookie),
):
    try:
        # db.query(models.User).filter(models.User.id == user.id).delete()
        db.delete(user)
        db.commit()

        # NOTE: now delete the access token also
        response = JSONResponse(content="files sucessfully deleted")
        response.delete_cookie(key="access_token")
        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"failed to delete the user instance {str(e)}"
        )
