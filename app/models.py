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


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    npi: Mapped[str] = mapped_column(String(10))


class PriorAuthStatus(enum.Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    DENIED = 'denied'
    MANUAL_REVIEW = 'manual_review'


class PriorAuthorization(Base):
    __tablename__ = "prior_authorizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    procedure_code: Mapped[str] = mapped_column(String(10))
    diagnosis_code: Mapped[str] = mapped_column(String(10))
    has_referral: Mapped[bool]
    pt_failed: Mapped[bool]
    status: Mapped[PriorAuthStatus]


class DecisionOutcome(enum.Enum):
    APPROVED = "approved"
    DENIED = "denied"
    MANUAL_REVIEW = "manual_review"


class AuthorizationDecision(Base):
    __tablename__ = "authorization_decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    prior_auth_id: Mapped[int] = mapped_column(ForeignKey("prior_authorizations.id"))
    decision: Mapped[DecisionOutcome]
    reason: Mapped[str] = mapped_column(String(255))
