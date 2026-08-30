from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Coverage, InsurancePlan, Member
from app.schemas import CoverageRead, MemberCreate, MemberRead

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

