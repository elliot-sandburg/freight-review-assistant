"""
Unit test suite for Freight Invoice & Receiving Review Assistant.
Tested using pytest.
"""

import math
import pytest
from project import (
    verify_manifest_weight,
    audit_accessorial_charges,
    calculate_rate_variance,
    main,
    STATUS_WITHIN_TOLERANCE,
    STATUS_REVIEW_REQUIRED,
    STATUS_COMPLIANT,
    STATUS_EXCEEDS_AGREED_RATE,
    STATUS_UNLISTED_SERVICE
)


def test_verify_manifest_weight():
    # 1. Exact match (0.0% variance)
    diff, var_pct, status = verify_manifest_weight(4000.0, 4000.0, tolerance_pct=0.05)
    assert diff == 0.0
    assert var_pct == 0.0
    assert status == STATUS_WITHIN_TOLERANCE

    # 2. Exact upper boundary (+5.0%)
    diff, var_pct, status = verify_manifest_weight(4000.0, 4200.0, tolerance_pct=0.05)
    assert diff == 200.0
    assert var_pct == 5.0
    assert status == STATUS_WITHIN_TOLERANCE

    # 3. Decimal precision boundary test (1.0 to 1.1 at 0.10 tolerance)
    diff, var_pct, status = verify_manifest_weight(1.0, 1.1, tolerance_pct=0.10)
    assert status == STATUS_WITHIN_TOLERANCE

    # 4. Just over upper boundary (5.0025% -> REVIEW_REQUIRED)
    diff, var_pct, status = verify_manifest_weight(4000.0, 4200.1, tolerance_pct=0.05)
    assert diff == 200.1
    assert var_pct == 5.0
    assert status == STATUS_REVIEW_REQUIRED

    # 5. Exact lower boundary (-5.0%)
    diff, var_pct, status = verify_manifest_weight(4000.0, 3800.0, tolerance_pct=0.05)
    assert diff == -200.0
    assert var_pct == -5.0
    assert status == STATUS_WITHIN_TOLERANCE

    # 6. Type and non-finite validations
    with pytest.raises(ValueError):
        verify_manifest_weight(0, 4000.0)
    with pytest.raises(ValueError):
        verify_manifest_weight(4000.0, -10.0)
    with pytest.raises(ValueError):
        verify_manifest_weight(4000.0, 4200.0, tolerance_pct=-0.01)
    with pytest.raises(ValueError):
        verify_manifest_weight(float("nan"), 4200.0)
    with pytest.raises(TypeError):
        verify_manifest_weight(True, 4200.0)


def test_audit_accessorial_charges():
    contract = {
        "liftgate": 65.00,
        "NOTIFY": 20.00
    }

    # 1. Fully compliant billing with case insensitivity check
    billing = {"LIFTGATE": 65.00, "notify": 15.00}
    total_flagged, log = audit_accessorial_charges(billing, contract)
    assert total_flagged == 0.0
    assert len(log) == 2
    assert all(item["status"] == STATUS_COMPLIANT for item in log)

    # 2. Rate overage and unlisted code in single run
    mixed_billing = {
        "LIFTGATE": 85.00,    # +$20 overage
        "DETENTION": 120.00   # unlisted
    }
    total_flagged, log = audit_accessorial_charges(mixed_billing, contract)
    assert total_flagged == 140.00
    assert log[0]["code"] == "LIFTGATE"
    assert log[0]["contract"] == 65.00
    assert log[0]["variance"] == 20.00
    assert log[0]["status"] == STATUS_EXCEEDS_AGREED_RATE

    assert log[1]["code"] == "DETENTION"
    assert log[1]["contract"] is None
    assert log[1]["variance"] == 120.00
    assert log[1]["status"] == STATUS_UNLISTED_SERVICE

    # 3. Collision in contract schedule raises ValueError
    with pytest.raises(ValueError):
        audit_accessorial_charges({}, {"LIFTGATE": 65.0, " liftgate ": 75.0})

    # 4. Collision in billed charges raises ValueError
    with pytest.raises(ValueError):
        audit_accessorial_charges({"LIFTGATE": 65.0, " liftgate ": 85.0}, contract)

    # 5. Empty or whitespace code raises ValueError
    with pytest.raises(ValueError):
        audit_accessorial_charges({"": 50.0}, contract)
    with pytest.raises(ValueError):
        audit_accessorial_charges({}, {"   ": 50.0})

    # 6. Negative values, Booleans, and NaNs raise errors
    with pytest.raises(ValueError):
        audit_accessorial_charges({}, {"HAZMAT": -50.0})
    with pytest.raises(TypeError):
        audit_accessorial_charges({"LIFTGATE": True}, contract)
    with pytest.raises(ValueError):
        audit_accessorial_charges({"LIFTGATE": float("nan")}, contract)
    with pytest.raises(TypeError):
        audit_accessorial_charges("not-a-dict", contract)


def test_calculate_rate_variance():
    # 1. Exact match
    res = calculate_rate_variance(500.00, 500.00, tolerance_pct=0.02)
    assert res["diff"] == 0.0
    assert res["variance_pct"] == 0.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # 2. Exact upper boundary (+2.0%)
    res = calculate_rate_variance(500.00, 510.00, tolerance_pct=0.02)
    assert res["diff"] == 10.00
    assert res["variance_pct"] == 2.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # 3. Decimal precision boundary test (1.0 to 1.1 at 0.10 tolerance)
    res = calculate_rate_variance(1.0, 1.1, tolerance_pct=0.10)
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # 4. Just over upper boundary (2.002% -> REVIEW_REQUIRED)
    res = calculate_rate_variance(500.00, 510.01, tolerance_pct=0.02)
    assert res["diff"] == 10.01
    assert res["status"] == STATUS_REVIEW_REQUIRED

    # 5. Billed less than quote -> within ceiling tolerance
    res = calculate_rate_variance(500.00, 450.00, tolerance_pct=0.02)
    assert res["diff"] == -50.00
    assert res["variance_pct"] == -10.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # 6. Type, boolean, and non-finite validation
    with pytest.raises(ValueError):
        calculate_rate_variance(0, 500.00)
    with pytest.raises(TypeError):
        calculate_rate_variance(True, 500.00)
    with pytest.raises(ValueError):
        calculate_rate_variance(500.00, float("nan"))


def test_main_report(capsys):
    """Smoke test to verify report prints without error."""
    main()
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "PO-99482-EUG" in captured.out
    assert "Total Surcharge Amount Requiring Review: $140.00" in captured.out
    assert "RECONCILIATION SUMMARY:" in captured.out