import json

import redis
from fastapi import Depends, FastAPI, HTTPException, Header
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.cache import redis_client

from app.models import (
    AuthorizationDecision,
    Coverage,
    CoverageStatus,
    DecisionOutcome,
    InsurancePlan,
    Member,
    PriorAuthorization,
    PriorAuthStatus,
    Claim,
    ClaimLine,
    ClaimStatus,
    AuditEvent,
    IdempotencyRecord
)
from app.schemas import (CoverageRead, MemberCreate, MemberRead, PriorAuthorizationCreate, PriorAuthorizationRead, AuthorizationDecisionRead, ClaimRead, ClaimCreate, ClaimLineRead, ClaimAdjudicationRequest)
from app.rules import evaluate_prior_auth, calculate_adjudication
from app.auth import RequireRole, get_current_identity, provider_has_relationship

app = FastAPI()


@app.post("/members", response_model=MemberRead)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    db_member = Member(
        first_name=member.first_name,
        last_name=member.last_name,
        date_of_birth=member.date_of_birth,
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@app.get("/members/{member_id}", response_model=MemberRead)
def read_member(
    member_id: int,
    db: Session = Depends(get_db),
    identity: dict = Depends(get_current_identity),
):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    if identity["role"] == "provider":
        if not provider_has_relationship(db, identity["provider_id"], member_id):
            raise HTTPException(status_code=404, detail="Member not found")
    elif identity["role"] != "reviewer":
        raise HTTPException(status_code=403, detail="Forbidden")

    return member


@app.get("/members/{member_id}/coverage", response_model=list[CoverageRead])
def read_member_coverage(
    member_id: int,
    db: Session = Depends(get_db),
    identity: dict = Depends(get_current_identity),
):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    if identity["role"] == "provider":
        if not provider_has_relationship(db, identity["provider_id"], member_id):
            raise HTTPException(status_code=404, detail="Member not found")
    elif identity["role"] != "reviewer":
        raise HTTPException(status_code=403, detail="Forbidden")

    cache_key = f"coverage:{member_id}"
    try:
        cached = redis_client.get(cache_key)
    except redis.RedisError:
        cached = None

    if cached is not None:
        return [CoverageRead.model_validate(item) for item in json.loads(cached)]

    stmt = (
        select(Coverage, InsurancePlan)
        .join(InsurancePlan, Coverage.plan_id == InsurancePlan.id)
        .where(Coverage.member_id == member_id)
    )
    rows = db.execute(stmt).all()

    result = [
        CoverageRead(
            status=coverage.status,
            plan_name=plan.plan_name,
            plan_type=plan.plan_type,
        )
        for coverage, plan in rows
    ]

    try:
        redis_client.setex(
            cache_key,
            60,
            json.dumps([item.model_dump(mode="json") for item in result]),
        )
    except redis.RedisError:
        pass

    return result


@app.post("/prior-authorizations", response_model=PriorAuthorizationRead)
def create_prior_authorization(
    prior: PriorAuthorizationCreate,
    db: Session = Depends(get_db),
    identity: dict = Depends(RequireRole("provider"))
):
    db_prior_authorization = PriorAuthorization(
        member_id=prior.member_id,
        provider_id=prior.provider_id,
        procedure_code=prior.procedure_code,
        diagnosis_code=prior.diagnosis_code,
        has_referral=prior.has_referral,
        pt_failed=prior.pt_failed,
        status=PriorAuthStatus.PENDING,
    )
    db.add(db_prior_authorization)
    db.commit()
    db.refresh(db_prior_authorization)
    return db_prior_authorization


@app.get("/prior-authorizations/{prior_auth_id}", response_model=PriorAuthorizationRead)
def read_prior_authorization(prior_auth_id: int, db: Session = Depends(get_db)):
    prior_authorization = db.get(PriorAuthorization, prior_auth_id)
    if prior_authorization is None:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    return prior_authorization


@app.post("/prior-authorizations/{prior_auth_id}/decision", response_model=AuthorizationDecisionRead)
def create_authorization_decision(
    prior_auth_id: int,
    db: Session = Depends(get_db),
    identity: dict = Depends(RequireRole("reviewer"))
):
    prior_authorization = db.get(PriorAuthorization, prior_auth_id)
    if prior_authorization is None:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    coverage = (
        db.execute(select(Coverage).where(Coverage.member_id == prior_authorization.member_id))
        .scalars()
        .first()
    )
    coverage_active = coverage is not None and coverage.status == CoverageStatus.ACTIVE

    decision, reason = evaluate_prior_auth(
        coverage_active=coverage_active,
        has_referral=prior_authorization.has_referral,
        pt_failed=prior_authorization.pt_failed,
    )

    db_decision = AuthorizationDecision(
        prior_auth_id=prior_authorization.id,
        decision=decision,
        reason=reason,
    )
    db.add(db_decision)

    prior_authorization.status = PriorAuthStatus[decision.name]

    db.commit()
    db.refresh(db_decision)
    return db_decision


@app.post("/claims", response_model=ClaimRead)
def create_claim(
    claim: ClaimCreate,
    db: Session = Depends(get_db),
    identity: dict = Depends(RequireRole("provider")),
    idempotency_key: str = Header()
):
    existing_record = db.execute(
        select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
    ).scalars().first()

    if existing_record is not None:
        return db.get(Claim, existing_record.claim_id)

    db_claim = Claim(
        member_id=claim.member_id,
        provider_id=claim.provider_id,
        status=ClaimStatus.SUBMITTED
    )
    db.add(db_claim)
    db.flush()
    for line in claim.lines:
        db_line = ClaimLine(
            claim_id=db_claim.id,
            procedure_code=line.procedure_code,
            submitted_amount=line.submitted_amount,
        )
        db.add(db_line)

    db_idempotency_record = IdempotencyRecord(
        idempotency_key=idempotency_key,
        claim_id=db_claim.id,
    )
    db.add(db_idempotency_record)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        winning_record = db.execute(
            select(IdempotencyRecord).where(IdempotencyRecord.idempotency_key == idempotency_key)
        ).scalars().first()
        return db.get(Claim, winning_record.claim_id)

    db.refresh(db_claim)
    return db_claim


@app.post("/claims/{claim_id}/adjudicate", response_model=ClaimRead)
def adjudicate_claim(
    claim_id: int,
    adjudication: ClaimAdjudicationRequest,
    db: Session = Depends(get_db),
    identity: dict = Depends(RequireRole("reviewer"))
):
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    result = db.execute(
        update(Claim)
        .where(Claim.id == claim_id, Claim.status == ClaimStatus.SUBMITTED)
        .values(status=ClaimStatus.ADJUDICATED)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=409, detail="Claim has already been adjudicated")

    claim.status = ClaimStatus.ADJUDICATED

    allowed_amounts = {
        item.line_id: item.allowed_amount for item in adjudication.line_allowed_amounts
    }

    for line in claim.lines:
        line.allowed_amount = allowed_amounts[line.id]
        line.insurance_paid, line.patient_responsibility = calculate_adjudication(
            submitted_amount=line.submitted_amount,
            allowed_amount=line.allowed_amount,
        )

    db_audit_event = AuditEvent(
        claim_id=claim.id,
        event_type="CLAIM_ADJUDICATED",
        description="Claim lines adjudicated and status updated",
    )
    db.add(db_audit_event)

    db.commit()
    db.refresh(claim)
    return claim


@app.get("/claims/{claim_id}", response_model=ClaimRead)
def read_claim(claim_id: int, db: Session = Depends(get_db), identity: dict = Depends(RequireRole("provider"))):
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.provider_id == identity["provider_id"]:
        return claim
    else:
        raise HTTPException(status_code=404, detail="Claim not found")
