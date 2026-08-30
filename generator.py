import argparse
import random
from datetime import date, timedelta

from app.database import SessionLocal
from app.models import Coverage, CoverageStatus, InsurancePlan, Member

FIRST_NAMES = ["Jane", "John", "Maria", "Wei", "Aisha", "Carlos", "Priya", "Sam"]
LAST_NAMES = ["Doe", "Smith", "Garcia", "Chen", "Khan", "Rossi", "Patel", "Lee"]

PLANS = [
    ("Blue Shield PPO 500", "PPO"),
    ("Kaiser HMO Gold", "HMO"),
    ("Aetna EPO Silver", "EPO"),
]


def random_birthdate() -> date:
    start = date(1950, 1, 1)
    end = date(2005, 12, 31)
    days_between = (end - start).days
    return start + timedelta(days=random.randint(0, days_between))


def seed_plans(db) -> list[InsurancePlan]:
    existing = db.query(InsurancePlan).all()
    if existing:
        return existing

    plans = [InsurancePlan(plan_name=name, plan_type=ptype) for name, ptype in PLANS]
    db.add_all(plans)
    db.commit()
    return plans


def seed_members_with_coverage(db, plans: list[InsurancePlan], count: int) -> None:
    for _ in range(count):
        member = Member(
            first_name=random.choice(FIRST_NAMES),
            last_name=random.choice(LAST_NAMES),
            date_of_birth=random_birthdate(),
        )
        db.add(member)
        db.flush()  # assigns member.id without committing yet

        coverage = Coverage(
            member_id=member.id,
            plan_id=random.choice(plans).id,
            status=random.choice(list(CoverageStatus)),
        )
        db.add(coverage)

    db.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10, help="number of members to generate")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        plans = seed_plans(db)
        seed_members_with_coverage(db, plans, args.count)
        print(f"Seeded {len(plans)} plans and {args.count} members with coverage.")
    finally:
        db.close()
