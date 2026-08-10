from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_customers: int
    total_service_providers: int
    total_services: int
    total_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: float


class ProviderDashboardStats(BaseModel):
    today_appointments: int
    upcoming_appointments: int
    completed_appointments: int
    total_earnings: float
    average_rating: float
