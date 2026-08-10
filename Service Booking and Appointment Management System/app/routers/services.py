from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, Body
from app.utils.helpers import uploads_path_to_url
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user, get_current_user_optional
from app.core.permissions import require_roles
from app.database import get_db
from app.models.user import User
from app.models.service import Service
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from app.services.cache_service import CacheService

router = APIRouter()


@router.post("", response_model=ServiceOut)
def create_service(
    payload: ServiceCreate = Body(..., description="Provide `duration` as a human-friendly string, e.g. '1hr 30min', '45min', or '2hr'."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    require_roles(current_user, {"Service Provider", "Admin"})
    data = payload.model_dump()
    # validate duration input exists
    dur = data.get("duration")
    if not dur:
        raise HTTPException(status_code=400, detail="duration is required")
    data["duration"] = dur
    service = Service(**data, provider_id=current_user.id)
    created = ServiceRepository(db).create(service)
    CacheService().clear_namespace("services")
    # serialize and add full URL for provider profile image
    result = ServiceOut.model_validate(created).model_dump()
    if result.get("provider_profile_image") and request is not None:
        result["provider_profile_image"] = uploads_path_to_url(str(request.base_url), result["provider_profile_image"])
    if result.get("service_image") and request is not None:
        result["service_image"] = uploads_path_to_url(str(request.base_url), result["service_image"])
    return result


@router.get("", response_model=list[ServiceOut])
def list_services(
    category: str | None = None,
    search: str | None = None,
    status: str | None = "active",
    min_price: float | None = None,
    max_price: float | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    request: Request = None,
):
    cache = CacheService()
    provider_id = None
    if current_user and current_user.role == "Service Provider":
        provider_id = current_user.id
    cache_key = f"services:{category}:{search}:{status}:{min_price}:{max_price}:{skip}:{limit}:{provider_id or 'all'}"
    cached = cache.get(cache_key)
    if cached is not None:
        # cached entries store internal paths (no host). Convert to full URLs for this response.
        response_result = []
        for item in cached:
            copy_item = dict(item)
            p = copy_item.get("provider_profile_image")
            if p:
                copy_item["provider_profile_image"] = uploads_path_to_url(str(request.base_url), p) if request is not None else p
            s = copy_item.get("service_image")
            if s:
                copy_item["service_image"] = uploads_path_to_url(str(request.base_url), s) if request is not None else s
            response_result.append(copy_item)
        return response_result
    services = ServiceRepository(db).get_all(
        skip=skip,
        limit=limit,
        category=category,
        search=search,
        status=status,
        min_price=min_price,
        max_price=max_price,
        provider_id=provider_id,
    )
    raw = [ServiceOut.model_validate(service).model_dump() for service in services]
    # cache raw entries (store internal paths, not host-specific URLs)
    cache.set(cache_key, raw, ttl=300)
    # build response with full URLs
    response_result = []
    for item in raw:
        copy_item = dict(item)
        p = copy_item.get("provider_profile_image")
        if p and request is not None:
            copy_item["provider_profile_image"] = uploads_path_to_url(str(request.base_url), p)
        s = copy_item.get("service_image")
        if s and request is not None:
            copy_item["service_image"] = uploads_path_to_url(str(request.base_url), s)
        response_result.append(copy_item)
    return response_result


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(
    service_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
    request: Request = None,
):
    service = ServiceRepository(db).get_by_id(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if current_user and current_user.role == "Service Provider" and service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view services owned by another provider",
        )
    result = ServiceOut.model_validate(service).model_dump()
    p = result.get("provider_profile_image")
    if p and request is not None:
        result["provider_profile_image"] = uploads_path_to_url(str(request.base_url), p)
    s = result.get("service_image")
    if s and request is not None:
        result["service_image"] = uploads_path_to_url(str(request.base_url), s)
    return result


@router.put("/{service_id}", response_model=ServiceOut)
def update_service(
    service_id: int,
    payload: ServiceUpdate = Body(..., description="Fields to update. Use `duration` as a human-friendly string, e.g. '1hr 30min'."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    require_roles(current_user, {"Service Provider", "Admin"})
    service = ServiceRepository(db).get_by_id(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if current_user.role != "Admin" and service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update services owned by another provider",
        )
    updates = payload.model_dump(exclude_unset=True)
    if "duration" in updates:
        updates["duration"] = updates["duration"]
    for key, value in updates.items():
        setattr(service, key, value)
    updated = ServiceRepository(db).update(service)
    CacheService().clear_namespace("services")
    result = ServiceOut.model_validate(updated).model_dump()
    p = result.get("provider_profile_image")
    if p and request is not None:
        result["provider_profile_image"] = uploads_path_to_url(str(request.base_url), p)
    s = result.get("service_image")
    if s and request is not None:
        result["service_image"] = uploads_path_to_url(str(request.base_url), s)
    return result
    


@router.delete("/{service_id}")
def delete_service(service_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_roles(current_user, {"Service Provider", "Admin"})
    service = ServiceRepository(db).get_by_id(service_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    if current_user.role != "Admin" and service.provider_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete services owned by another provider",
        )
    ServiceRepository(db).delete(service)
    CacheService().clear_namespace("services")
    return {"message": "Service deleted"}
