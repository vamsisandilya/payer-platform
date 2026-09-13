import argparse
import random
import time
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import insert

from app.database import SessionLocal, engine
from app.models import Claim, ClaimLine, ClaimStatus, Coverage, CoverageStatus, InsurancePlan, Member, Provider

FIRST_NAMES = ["Jane", "John", "Maria", "Wei", "Aisha", "Carlos", "Priya", "Sam"]
LAST_NAMES = ["Doe", "Smith", "Garcia", "Chen", "Khan", "Rossi", "Patel", "Lee"]

PLANS = [
    ("Blue Shield PPO 500", "PPO"),
    ("Kaiser HMO Gold", "HMO"),
    ("Aetna EPO Silver", "EPO"),
]

PROVIDER_COUNT = 20

PROCEDURE_CODES = ["99213", "99214", "80053", "73721", "71046"]


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


def random_npi() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(10))


def seed_providers(db, count: int = PROVIDER_COUNT) -> list[Provider]:
    existing = db.query(Provider).all()
    if existing:
        return existing

    providers = [
        Provider(
            provider_name=f"Dr. {random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            npi=random_npi(),
        )
        for _ in range(count)
    ]
    db.add_all(providers)
    db.commit()
    return providers


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


def seed_claims_naive(db, members: list[Member], providers: list[Provider], count: int) -> float:
    start = time.perf_counter()

    for _ in range(count):
        claim = Claim(
            member_id=random.choice(members).id,
            provider_id=random.choice(providers).id,
            status=ClaimStatus.SUBMITTED,
        )
        db.add(claim)
        db.flush()  # need claim.id before the line can reference it

        line = ClaimLine(
            claim_id=claim.id,
            procedure_code=random.choice(PROCEDURE_CODES),
            submitted_amount=Decimal(random.randint(50, 500)),
        )
        db.add(line)

    db.commit()

    return time.perf_counter() - start


def seed_claims_batched(
    db, members: list[Member], providers: list[Provider], count: int, batch_size: int = 5000
) -> float:
    start = time.perf_counter()

    remaining = count
    while remaining > 0:
        batch_count = min(batch_size, remaining)

        claim_rows = [
            {
                "member_id": random.choice(members).id,
                "provider_id": random.choice(providers).id,
                "status": ClaimStatus.SUBMITTED,
            }
            for _ in range(batch_count)
        ]
        result = db.execute(insert(Claim).returning(Claim.id), claim_rows)
        claim_ids = [row[0] for row in result]

        line_rows = [
            {
                "claim_id": claim_id,
                "procedure_code": random.choice(PROCEDURE_CODES),
                "submitted_amount": Decimal(random.randint(50, 500)),
            }
            for claim_id in claim_ids
        ]
        db.execute(insert(ClaimLine), line_rows)

        remaining -= batch_count

    db.commit()

    return time.perf_counter() - start


if __name__ == "__main__":
    engine.echo = False  # quiet SQL echo for volume timing runs

    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10, help="number of members to generate")
    parser.add_argument("--claims-naive", type=int, default=0, help="number of claims to seed the naive, one-at-a-time way (timed)")
    parser.add_argument("--claims-batched", type=int, default=0, help="number of claims to seed the batched way (timed)")
    parser.add_argument("--batch-size", type=int, default=5000, help="rows per batch for --claims-batched")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        plans = seed_plans(db)
        providers = seed_providers(db)
        seed_members_with_coverage(db, plans, args.count)
        print(f"Seeded {len(plans)} plans, {len(providers)} providers, and {args.count} members with coverage.")

        if args.claims_naive:
            members = db.query(Member).all()
            elapsed = seed_claims_naive(db, members, providers, args.claims_naive)
            print(f"Seeded {args.claims_naive} claims (naive, one-at-a-time) in {elapsed:.2f} seconds.")

        if args.claims_batched:
            members = db.query(Member).all()
            elapsed = seed_claims_batched(db, members, providers, args.claims_batched, args.batch_size)
            print(f"Seeded {args.claims_batched} claims (batched, size {args.batch_size}) in {elapsed:.2f} seconds.")
    finally:
        db.close()
