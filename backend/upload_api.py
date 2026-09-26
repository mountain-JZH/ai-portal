from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from auth_api import get_current_admin


router = APIRouter(
    prefix="/api/admin/uploads",
    tags=["Image uploads"],
    dependencies=[Depends(get_current_admin)],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_ROOT = PROJECT_ROOT / "uploads"
MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_CATEGORIES = {"banners", "news"}
IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


@router.post("/{category}")
async def upload_image(category: str, file: UploadFile = File(...)):
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload category",
        )

    extension = IMAGE_EXTENSIONS.get(file.content_type or "")

    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WebP images are allowed",
        )

    try:
        content = await file.read(MAX_IMAGE_SIZE + 1)
    finally:
        await file.close()

    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size must not exceed 5 MB",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is empty",
        )

    filename = f"{uuid4().hex}{extension}"
    category_directory = UPLOAD_ROOT / category
    destination = category_directory / filename

    try:
        category_directory.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    except OSError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image",
        ) from error

    return {
        "url": f"/uploads/{category}/{filename}",
        "filename": filename,
    }
