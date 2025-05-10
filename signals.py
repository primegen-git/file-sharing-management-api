import os
import models
from dotenv import load_dotenv
from sqlalchemy import event
import boto3
import logging

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Configure logging
logger = logging.getLogger(__name__)


# Initialize your S3 client
s3_client = boto3.client("s3", region_name=AWS_REGION)


@event.listens_for(models.File, "after_delete")
def delete_s3_object(mapper, connection, target):
    """
    Deletes the corresponding S3 object after the File record is deleted from the database.
    """
    try:
        s3_key = target.storage_path  # Ensure this attribute exists in your model
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        logger.info(f"Deleted S3 object: {s3_key}")
    except Exception as e:
        logger.error(f"Failed to delete S3 object {s3_key}: {e}")
