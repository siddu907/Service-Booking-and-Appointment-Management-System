from sqlalchemy.orm import Session

from app.models.service import Service


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, service: Service) -> Service:
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        return service

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        search: str | None = None,
        status: str | None = "active",
        min_price: float | None = None,
        max_price: float | None = None,
        provider_id: int | None = None,
    ):
        query = self.db.query(Service).filter(Service.is_deleted.is_(False))
        if provider_id is not None:
            query = query.filter(Service.provider_id == provider_id)
        if status:
            query = query.filter(Service.status == status)
        if category:
            # allow partial, case-insensitive matches for category
            term_cat = f"%{category}%"
            query = query.filter(Service.category.ilike(term_cat))
        if search:
            term = f"%{search}%"
            query = query.filter(
                Service.name.ilike(term)
                | Service.description.ilike(term)
                | Service.category.ilike(term)
            )
        if min_price is not None:
            query = query.filter(Service.price >= min_price)
        if max_price is not None:
            query = query.filter(Service.price <= max_price)
        
        query = query.order_by(Service.id.asc())
        return query.offset(skip).limit(limit).all()

    def get_by_id(self, service_id: int) -> Service | None:
        return self.db.query(Service).filter(Service.id == service_id, Service.is_deleted.is_(False)).first()

    def update(self, service: Service) -> Service:
        self.db.commit()
        self.db.refresh(service)
        return service

    def delete(self, service: Service) -> None:
        service.is_deleted = True
        self.db.commit()
