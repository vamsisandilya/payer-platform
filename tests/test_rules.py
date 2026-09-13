from decimal import Decimal

from app.models import DecisionOutcome
from app.rules import calculate_adjudication, evaluate_prior_auth


def test_denied_when_coverage_not_active():
    decision, reason = evaluate_prior_auth(coverage_active=False, has_referral=True, pt_failed=True)
    assert decision == DecisionOutcome.DENIED


def test_denied_when_coverage_not_active_regardless_of_other_facts():
    decision, reason = evaluate_prior_auth(coverage_active=False, has_referral=False, pt_failed=False)
    assert decision == DecisionOutcome.DENIED


def test_approved_when_active_referral_and_pt_failed():
    decision, reason = evaluate_prior_auth(coverage_active=True, has_referral=True, pt_failed=True)
    assert decision == DecisionOutcome.APPROVED


def test_manual_review_when_no_referral():
    decision, reason = evaluate_prior_auth(coverage_active=True, has_referral=False, pt_failed=True)
    assert decision == DecisionOutcome.MANUAL_REVIEW


def test_manual_review_when_no_referral_and_pt_not_failed():
    decision, reason = evaluate_prior_auth(coverage_active=True, has_referral=False, pt_failed=False)
    assert decision == DecisionOutcome.MANUAL_REVIEW


def test_manual_review_when_referral_present_but_pt_not_failed():
    decision, reason = evaluate_prior_auth(coverage_active=True, has_referral=True, pt_failed=False)
    assert decision == DecisionOutcome.MANUAL_REVIEW


def test_calculate_adjudication_normal_case():
    insurance_paid, patient_responsibility = calculate_adjudication(
        submitted_amount=Decimal("150.00"), allowed_amount=Decimal("120.00")
    )
    assert insurance_paid == Decimal("120.00")
    assert patient_responsibility == Decimal("30.00")


def test_calculate_adjudication_fully_covered():
    insurance_paid, patient_responsibility = calculate_adjudication(
        submitted_amount=Decimal("100.00"), allowed_amount=Decimal("100.00")
    )
    assert insurance_paid == Decimal("100.00")
    assert patient_responsibility == Decimal("0.00")


def test_calculate_adjudication_nothing_allowed():
    insurance_paid, patient_responsibility = calculate_adjudication(
        submitted_amount=Decimal("100.00"), allowed_amount=Decimal("0.00")
    )
    assert insurance_paid == Decimal("0.00")
    assert patient_responsibility == Decimal("100.00")


def test_calculate_adjudication_when_allowed_exceeds_submitted():
    insurance_paid, patient_responsibility = calculate_adjudication(
        submitted_amount=Decimal("100.00"), allowed_amount=Decimal("120.00")
    )
    assert patient_responsibility == Decimal("0.00")
