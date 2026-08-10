from sqlalchemy.orm import Session

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_by_provider(self, provider_id: int, skip: int = 0, limit: int = 100):
        return self.db.query(Review).filter(Review.provider_id == provider_id).offset(skip).limit(limit).all()

    def get_by_booking_id(self, booking_id: int) -> Review | None:
        return self.db.query(Review).filter(Review.booking_id == booking_id).first()

    def get_by_id(self, review_id: int) -> Review | None:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def update(self, review: Review) -> Review:
        self.db.commit()
        self.db.refresh(review)
        return review

    def delete(self, review: Review) -> None:
        self.db.delete(review)
        self.db.commit()
