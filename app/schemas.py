from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models import CoverageStatus


class MemberCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date


class MemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    date_of_birth: date


class CoverageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: CoverageStatus
    plan_name: str
    plan_type: str
