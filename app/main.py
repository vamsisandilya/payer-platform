from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import (
    AuthorizationDecision,
    Coverage,
    CoverageStatus,
    DecisionOutcome,
    InsurancePlan,
    Member,
    PriorAuthorization,
    PriorAuthStatus,
)
from app.schemas import CoverageRead, MemberCreate, MemberRead, PriorAuthorizationCreate, PriorAuthorizationRead, AuthorizationDecisionRead
from app.rules import evaluate_prior_auth

Base.metadata.create_all(bind=engine)

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
def read_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@app.get("/members/{member_id}/coverage", response_model=list[CoverageRead])
def read_member_coverage(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")

    stmt = (
        select(Coverage, InsurancePlan)
        .join(InsurancePlan, Coverage.plan_id == InsurancePlan.id)
        .where(Coverage.member_id == member_id)
    )
    rows = db.execute(stmt).all()

    return [
        CoverageRead(
            status=coverage.status,
            plan_name=plan.plan_name,
            plan_type=plan.plan_type,
        )
        for coverage, plan in rows
    ]


@app.post("/prior-authorizations", response_model=PriorAuthorizationRead)
def create_prior_authorization(prior: PriorAuthorizationCreate, db: Session = Depends(get_db)):
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
def create_authorization_decision(prior_auth_id: int, db: Session = Depends(get_db)):
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
