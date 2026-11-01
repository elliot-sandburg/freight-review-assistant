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
    STATUS_UNLISTED_SERVICE,
)


def test_verify_manifest_weight():
    # Exact match
    diff, pct, status = verify_manifest_weight(4000, 4000, 0.05)
    assert diff == 0.0
    assert pct == 0.0
    assert status == STATUS_WITHIN_TOLERANCE

    # Exactly on positive boundary (4000 * 0.05 = 200 lb allowance)
    diff, pct, status = verify_manifest_weight(4000, 4200, 0.05)
    assert diff == 200.0
    assert pct == 5.0
    assert status == STATUS_WITHIN_TOLERANCE

    # Exactly on negative boundary
    diff, pct, status = verify_manifest_weight(4000, 3800, 0.05)
    assert diff == -200.0
    assert pct == -5.0
    assert status == STATUS_WITHIN_TOLERANCE

    # Decimal representation edge case (1.1 - 1.0 = 0.1)
    diff, pct, status = verify_manifest_weight(1.0, 1.1, 0.1)
    assert status == STATUS_WITHIN_TOLERANCE

    # Just exceeding upper boundary (strict threshold test)
    diff, pct, status = verify_manifest_weight(4000, 4200.0000001, 0.05)
    assert status == STATUS_REVIEW_REQUIRED

    # Just exceeding lower boundary
    diff, pct, status = verify_manifest_weight(4000, 3799.9, 0.05)
    assert status == STATUS_REVIEW_REQUIRED

    # Input validations
    with pytest.raises(TypeError):
        verify_manifest_weight(True, 4000, 0.05)
    with pytest.raises(TypeError):
        verify_manifest_weight("4000", 4000, 0.05)
    with pytest.raises(ValueError):
        verify_manifest_weight(0, 4000, 0.05)
    with pytest.raises(ValueError):
        verify_manifest_weight(-100, 4000, 0.05)
    with pytest.raises(ValueError):
        verify_manifest_weight(4000, float("nan"), 0.05)


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

    items_by_code = {item["code"]: item for item in log}
    assert items_by_code["LIFTGATE"]["status"] == STATUS_EXCEEDS_AGREED_RATE
    assert items_by_code["LIFTGATE"]["variance"] == 20.00

    assert items_by_code["NOTIFY"]["status"] == STATUS_COMPLIANT
    assert items_by_code["NOTIFY"]["variance"] == 0.00

    assert items_by_code["DETENTION"]["status"] == STATUS_UNLISTED_SERVICE
    assert items_by_code["DETENTION"]["contract"] is None
    assert items_by_code["DETENTION"]["variance"] == 120.00

    # Line item variances must sum exactly to the total review amount
    assert sum(item["variance"] for item in log) == total

    # Empty schedules
    empty_total, empty_log = audit_accessorial_charges({}, {})
    assert empty_total == 0.0
    assert empty_log == []

    # Duplicate key collisions
    with pytest.raises(ValueError):
        audit_accessorial_charges({"liftgate": 50, " LIFTGATE ": 60}, {})
    with pytest.raises(ValueError):
        audit_accessorial_charges({}, {"notify": 10, "NOTIFY": 10})

    # Empty or whitespace-only service codes
    with pytest.raises(ValueError):
        audit_accessorial_charges({"": 50}, {})
    with pytest.raises(ValueError):
        audit_accessorial_charges({"   ": 50}, {})

    # Non-string service codes
    with pytest.raises(ValueError):
        audit_accessorial_charges({123: 50}, {})

    # Type and value validations
    with pytest.raises(TypeError):
        audit_accessorial_charges({"A": True}, {})
    with pytest.raises(ValueError):
        audit_accessorial_charges({"A": -10}, {})
    with pytest.raises(TypeError):
        audit_accessorial_charges("not a dict", {})


def test_calculate_rate_variance():
    # Exact match
    res = calculate_rate_variance(450.00, 450.00, 0.02)
    assert res["diff"] == 0.0
    assert res["variance_pct"] == 0.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # Lower billed rate (one-sided check is within tolerance)
    res = calculate_rate_variance(450.00, 400.00, 0.02)
    assert res["diff"] == -50.0
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # Exactly on positive threshold (450 * 0.02 = 9.00 -> 459.00)
    res = calculate_rate_variance(450.00, 459.00, 0.02)
    assert res["status"] == STATUS_WITHIN_TOLERANCE

    # Exceeding positive threshold
    res = calculate_rate_variance(450.00, 475.00, 0.02)
    assert res["diff"] == 25.0
    assert res["variance_pct"] == 5.56
    assert res["status"] == STATUS_REVIEW_REQUIRED

    # Large magnitude strict boundary test
    res = calculate_rate_variance(1_000_000_000, 1_020_000_000.01, 0.02)
    assert res["status"] == STATUS_REVIEW_REQUIRED

    # Schema verification
    assert set(res.keys()) == {"quoted", "billed", "diff", "variance_pct", "status"}

    # Validation errors
    with pytest.raises(TypeError):
        calculate_rate_variance(True, 450, 0.02)
    with pytest.raises(ValueError):
        calculate_rate_variance(0, 450, 0.02)
    with pytest.raises(ValueError):
        calculate_rate_variance(450, -10, 0.02)
    with pytest.raises(ValueError):
        calculate_rate_variance(450, 450, -0.01)


def test_main(capsys):
    ret = main()
    assert ret is None
    captured = capsys.readouterr()
    assert "FREIGHT AUDIT REVIEW SUMMARY" in captured.out
    assert "PO-2026-8841" in captured.out
    assert "Total Surcharge Review Amount: $140.00" in captured.out
    assert "AUDIT FINDINGS DISCLAIMER" in captured.out