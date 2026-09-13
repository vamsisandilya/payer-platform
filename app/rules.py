from decimal import Decimal

from app.models import DecisionOutcome


def evaluate_prior_auth(coverage_active: bool, has_referral: bool, pt_failed: bool) -> tuple[DecisionOutcome, str]:
    if not coverage_active:
        return (DecisionOutcome.DENIED, "Member's coverage is not active")
    elif has_referral and pt_failed:
        return (DecisionOutcome.APPROVED, "Active coverage, referral on file and physical therapy already failed")
    elif not has_referral:
        return (DecisionOutcome.MANUAL_REVIEW, "No referral on file")
    else:
        return (DecisionOutcome.MANUAL_REVIEW, "Physical therapy has not been tried yet")


def calculate_adjudication(submitted_amount: Decimal, allowed_amount: Decimal) -> tuple[Decimal, Decimal]:
    insurance_paid = min(allowed_amount, submitted_amount)
    patient_responsibility = submitted_amount - insurance_paid
    return insurance_paid, patient_responsibility
