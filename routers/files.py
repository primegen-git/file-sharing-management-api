from fastapi import APIRouter, Depends
from dependecies import get_current_user_from_cookie


router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(get_current_user_from_cookie)],
)
