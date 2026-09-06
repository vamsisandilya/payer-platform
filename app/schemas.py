from datetime import date

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models import CoverageStatus, PriorAuthStatus, DecisionOutcome, ClaimStatus


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


class PriorAuthorizationCreate(BaseModel):
    member_id: int
    provider_id: int
    procedure_code: str
    diagnosis_code: str
    has_referral: bool
    pt_failed: bool


class PriorAuthorizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    provider_id: int
    procedure_code: str
    diagnosis_code: str
    has_referral: bool
    pt_failed: bool
    status: PriorAuthStatus


class AuthorizationDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    decision: DecisionOutcome
    reason: str


class ClaimLineCreate(BaseModel):
    procedure_code: str
    submitted_amount: Decimal


class ClaimCreate(BaseModel):
    member_id: int
    provider_id: int
    lines: list[ClaimLineCreate]


class ClaimLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    procedure_code: str
    submitted_amount: Decimal
    allowed_amount: Decimal | None
    insurance_paid: Decimal | None
    patient_responsibility: Decimal | None


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    provider_id: int
    status: ClaimStatus
    lines: list[ClaimLineRead]


class ClaimLineAllowedAmount(BaseModel):
    line_id: int
    allowed_amount: Decimal


class ClaimAdjudicationRequest(BaseModel):
    line_allowed_amounts: list[ClaimLineAllowedAmount]
