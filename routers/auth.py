from fastapi import APIRouter


router = APIRouter(
    prefix="/auth", tags=["auth"], responses={401: {"message": "unauthorized access"}}
)


@router.get("/")
async def auth():
    return {"mess": "inside the auth"}
