from datetime import date

from pydantic import BaseModel, ConfigDict


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
