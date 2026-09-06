import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
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


class ClaimStatus(enum.Enum):
    SUBMITTED = "submitted"
    ADJUDICATED = "adjudicated"


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    provider_id: Mapped[int] = mapped_column(ForeignKey("providers.id"))
    status: Mapped[ClaimStatus]
    lines: Mapped[list["ClaimLine"]] = relationship(back_populates="claim")


class ClaimLine(Base):
    __tablename__ = "claim_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    procedure_code: Mapped[str] = mapped_column(String(10))
    submitted_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    allowed_amount: Mapped[Decimal | None]
    insurance_paid: Mapped[Decimal | None]
    patient_responsibility: Mapped[Decimal | None]
    claim: Mapped["Claim"] = relationship(back_populates="lines")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
