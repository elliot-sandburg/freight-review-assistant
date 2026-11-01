import pytest
from project import (
    verify_manifest_weight,
    audit_accessorial_charges,
    calculate_rate_variance,
    STATUS_WITHIN_TOLERANCE,
    STATUS_REVIEW_REQUIRED,
    STATUS_COMPLIANT,
    STATUS_EXCEEDS_AGREED_RATE,
    STATUS_UNLISTED_SERVICE,
)


def test_verify_manifest_weight():
    # Exact match
    diff, pct, status = verify_manifest_weight(4000, 4000, 0.05)
    assert diff == 0.0
    assert pct == 0.0
    assert status == STATUS_WITHIN_TOLERANCE

    # Positive variance within 5% tolerance (4000 * 0.05 = 200 lb allowance)
    diff, pct, status = verify_manifest_weight(4000, 4150, 0.05)
    assert diff == 150.0
    assert pct == 3.75
    assert status == STATUS_WITHIN_TOLERANCE

    # Positive variance exceeding tolerance
    diff, pct, status = verify_manifest_weight(4000, 4300, 0.05)
    assert diff == 300.0
    assert pct == 7.5
    assert status == STATUS_REVIEW_REQUIRED

    # Negative variance exceeding tolerance (two-sided check)
    diff, pct, status = verify_manifest_weight(4000, 3700, 0.05)
    assert diff == -300.0
    assert pct == -7.5
    assert status == STATUS_REVIEW_REQUIRED

    # Invalid inputs
    with pytest.raises(TypeError):
        verify_manifest_weight("4000", 4000, 0.05)
    with pytest.raises(TypeError):
        verify_manifest_weight(True, 4000, 0.05)
    with pytest.raises(ValueError):
        verify_manifest_weight(0, 4000, 0.05)
    with pytest.raises(ValueError):
        verify_manifest_weight(-500, 4000, 0.05)


def test_audit_accessorial_charges():
    billed = {
        "liftgate": 85.00,
        "NOTIFY": 0.00,
        "detention ": 120.00,
    }
    contract = {
        " LIFTGATE ": 65.00,
        "notify": 0.00,
    }
    total, log = audit_accessorial_charges(billed, contract)
    assert total == 140.00
    assert len(log) == 3

    # Check line item findings
    items = {item["code"]: item for item in log}
    assert items["LIFTGATE"]["status"] == STATUS_EXCEEDS_AGREED_RATE
    assert items["LIFTGATE"]["variance"] == 20.00

    assert items["NOTIFY"]["status"] == STATUS_COMPLIANT
    assert items["NOTIFY"]["variance"] == 0.00

    assert items["DETENTION"]["status"] == STATUS_UNLISTED_SERVICE
    assert items["DETENTION"]["contract"] is None
    assert items["DETENTION"]["variance"] == 120.00

    # Line item variances sum to total
    assert sum(item["variance"] for item in log) == total

    # Empty schedules
    empty_total, empty_log = audit_accessorial_charges({}, {})
    assert empty_total == 0.0
    assert empty_log == []

    # Duplicate code collisions
    with pytest.raises(ValueError):
        audit_accessorial_charges({"liftgate": 50, " LIFTGATE ": 60}, {})

    # Invalid types
    with pytest.raises(TypeError):
        audit_accessorial_charges("not_a_dict", {})
    with pytest.raises(ValueError):
        audit_accessorial_charges({"": 50}, {})
    with pytest.raises(ValueError):
        audit_accessorial_charges({"A": -10}, {})


def test_calculate_rate_variance():
    # Exact rate match
    res = calculate_rate_variance(450.00, 450.00, 0.02)
    assert res["diff"] == 0.0
    assert res["variance_pct"] == 0.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # Lower billed rate (compliant under one-sided ceiling check)
    res = calculate_rate_variance(450.00, 420.00, 0.02)
    assert res["diff"] == -30.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # Increase exceeding tolerance (450 * 0.02 = 9.00 max increase)
    res = calculate_rate_variance(450.00, 475.00, 0.02)
    assert res["diff"] == 25.0
    assert res["variance_pct"] == 5.56
    assert res["status"] == STATUS_REVIEW_REQUIRED

    # Return dictionary schema check
    assert set(res.keys()) == {"quoted", "billed", "diff", "variance_pct", "status"}

    # Invalid inputs
    with pytest.raises(TypeError):
        calculate_rate_variance(None, 450, 0.02)
    with pytest.raises(ValueError):
        calculate_rate_variance(0, 450, 0.02)
    with pytest.raises(ValueError):
        calculate_rate_variance(450, -100, 0.02)