import enum
from datetime import date

from sqlalchemy import Date, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date)


class InsurancePlan(Base):
    __tablename__ = "insurance_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_name: Mapped[str] = mapped_column(String(100))
    plan_type: Mapped[str] = mapped_column(String(100))


class CoverageStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    TERMINATED = "terminated"


class Coverage(Base):
    __tablename__ = "coverages"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("insurance_plans.id"))
    status: Mapped[CoverageStatus]
