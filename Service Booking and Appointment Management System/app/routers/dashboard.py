from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.oauth2 import get_current_user
from app.core.permissions import require_roles
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStats, ProviderDashboardStats
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/admin", response_model=DashboardStats)
def admin_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_roles(current_user, {"Admin"})
    return DashboardService(db).admin_dashboard()


@router.get("/provider", response_model=ProviderDashboardStats)
def provider_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_roles(current_user, {"Service Provider"})
    return DashboardService(db).provider_dashboard(current_user.id)
