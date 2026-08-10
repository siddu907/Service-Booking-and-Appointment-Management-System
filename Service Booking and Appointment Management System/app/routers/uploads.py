from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.oauth2 import get_current_user
from app.core.permissions import require_roles
from app.database import get_db
from app.models.user import User
from app.repositories.service_repository import ServiceRepository
from app.repositories.user_repository import UserRepository
from app.services.cache_service import CacheService
from app.services.upload_service import UploadService
from urllib.parse import quote

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


def validate_image(file: UploadFile) -> None:
    if not file.filename or not file.filename.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must include a filename")
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image type. Allowed types: jpg, jpeg, png, webp",
        )
    try:
        file.file.seek(0, 2)
        size = file.file.tell()
        file.file.seek(0)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to validate uploaded image")
    if size > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum allowed size is {settings.max_upload_size} bytes",
        )


@router.post("/profile-image")
def upload_profile_image(
    request: Request,
    file: UploadFile = File(...),
    user_id: int | None = Query(None, description="User ID when an admin uploads a provider profile image"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_image(file)

    if user_id is None:
        target_user = current_user
    else:
        if current_user.role != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can upload profile images for other users.",
            )
        target_user = UserRepository(db).get_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
        if target_user.role != "Service Provider":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin can only upload profile images for service providers.",
            )

    upload_service = UploadService(settings.upload_dir)
    try:
        path = upload_service.save_upload(file, "profile_images")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save profile image") from exc

    target_user.profile_image = path
    db.commit()
    db.refresh(target_user)
    CacheService().clear_namespace("services")
    # Construct publicly accessible URL for the saved file.
    # Files are served from the StaticFiles mount at /uploads/files
    path_part = "/uploads/files" + path[len("/uploads") :]
    encoded = quote(path_part, safe="/")
    base = str(request.base_url).rstrip("/")
    file_url = f"{base}{encoded}"
    return {"message": "Profile image uploaded successfully", "path": path, "url": file_url}


@router.post("/service-image/{service_id}")
def upload_service_image(service_id: int, request: Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_roles(current_user, {"Service Provider", "Admin"})
    validate_image(file)
    service = ServiceRepository(db).get_by_id(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if current_user.role != "Admin" and service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to upload this service image. Only the service owner or an admin can perform this action.",
        )
    upload_service = UploadService(settings.upload_dir)
    try:
        path = upload_service.save_upload(file, "service_images")
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save service image") from exc

    service.service_image = path
    db.commit()
    db.refresh(service)
    CacheService().clear_namespace("services")
    path_part = "/uploads/files" + path[len("/uploads") :]
    encoded = quote(path_part, safe="/")
    base = str(request.base_url).rstrip("/")
    file_url = f"{base}{encoded}"
    return {"message": "Service image uploaded successfully", "path": path, "url": file_url}
