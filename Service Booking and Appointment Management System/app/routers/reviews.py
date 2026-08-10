from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user, get_current_user_optional
from app.database import get_db
from app.models.review import Review
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("", response_model=ReviewOut)
def create_review(payload: ReviewCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ReviewService(db).create_review(current_user.id, payload)


@router.get("/provider/{provider_id}", response_model=list[ReviewOut])
def list_provider_reviews(
    provider_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    if provider_id is None:
        if current_user is None or current_user.role != "Service Provider":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        provider_id = current_user.id
    elif current_user is not None and current_user.role != "Admin" and current_user.role != "Customer" and current_user.role != "Service Provider":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    elif current_user is not None and current_user.role == "Service Provider" and provider_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    return ReviewRepository(db).get_by_provider(provider_id, skip=skip, limit=limit)


@router.put("/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, payload: ReviewUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    review = ReviewRepository(db).get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return ReviewService(db).update_review(review, payload)


@router.delete("/{review_id}")
def delete_review(review_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    review = ReviewRepository(db).get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    ReviewService(db).delete_review(review)
    return {"message": "Review deleted"}
