from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.review import Review
from app.repositories.review_repository import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewUpdate


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReviewRepository(db)

    def create_review(self, user_id: int, review_in: ReviewCreate) -> Review:
        booking = self.db.query(Booking).filter(Booking.id == review_in.booking_id, Booking.is_deleted.is_(False)).first()
        if not booking or booking.customer_id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking for review")
        if booking.status != "Completed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only completed bookings can be reviewed")
        if review_in.rating < 1 or review_in.rating > 5:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")
        if self.repo.get_by_booking_id(review_in.booking_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A review already exists for this booking")

        review = Review(
            booking_id=review_in.booking_id,
            customer_id=user_id,
            provider_id=booking.provider_id,
            rating=review_in.rating,
            review=review_in.review,
            created_at=datetime.utcnow(),
        )
        return self.repo.create(review)

    def update_review(self, review: Review, review_in: ReviewUpdate) -> Review:
        if review_in.rating is not None:
            if review_in.rating < 1 or review_in.rating > 5:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rating must be between 1 and 5")
            review.rating = review_in.rating
        if review_in.review is not None:
            review.review = review_in.review
        return self.repo.update(review)

    def delete_review(self, review: Review) -> None:
        self.repo.delete(review)
