from datetime import date
from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DashboardRepository(db)

    def admin_dashboard(self):
        return self.repo.admin_stats()

    def provider_dashboard(self, provider_id: int):
        return self.repo.provider_stats(provider_id, date.today())
