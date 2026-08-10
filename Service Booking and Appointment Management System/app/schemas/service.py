from pydantic import BaseModel, ConfigDict, Field


class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    category: str
    duration: str = Field(...,example="1hr 30min")
    price: float
    status: str = "active"


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    duration: str | None = Field(None,example="1hr 30min")
    price: float | None = None
    status: str | None = None


class ServiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    category: str
    duration: str
    price: float
    status: str
    provider_id: int
    provider_name: str | None = None
    service_image: str | None = None
    provider_profile_image: str | None = None
