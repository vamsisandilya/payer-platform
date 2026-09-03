from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models import CoverageStatus, PriorAuthStatus, DecisionOutcome


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
