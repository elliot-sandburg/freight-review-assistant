# Operational review status constants
STATUS_WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_COMPLIANT = "COMPLIANT"
STATUS_EXCEEDS_AGREED_RATE = "EXCEEDS_AGREED_RATE"
STATUS_UNLISTED_SERVICE = "UNLISTED_SERVICE"


def _validate_number(val, name="Value", allow_zero=False):
    """Validates that an input is a valid positive or non-negative number."""
    if not isinstance(val, (int, float)) or isinstance(val, bool):
        raise TypeError(f"{name} must be an integer or float.")
    if allow_zero:
        if val < 0:
            raise ValueError(f"{name} cannot be negative.")
    else:
        if val <= 0:
            raise ValueError(f"{name} must be greater than zero.")
    return float(val)


def _normalize_schedule(schedule, schedule_name="Schedule"):
    """Normalizes fee codes (uppercase, stripped) and checks for duplicates."""
    if not isinstance(schedule, dict):
        raise TypeError(f"{schedule_name} must be a dictionary.")

    normalized = {}
    for code, amount in schedule.items():
        if not isinstance(code, str):
            raise ValueError(f"Service code {code!r} must be a string.")

        cleaned = code.strip().upper()
        if not cleaned:
            raise ValueError(f"Service code in {schedule_name} cannot be empty.")
        if cleaned in normalized:
            raise ValueError(
                f"Duplicate service code collision: '{cleaned}' in {schedule_name}."
            )

        _validate_number(amount, f"Amount for '{cleaned}'", allow_zero=True)
        normalized[cleaned] = round(float(amount), 2)

    return normalized


def verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05):
    """
    Checks if physical scale weight matches manifest weight within tolerance.
    Two-sided check: difference cannot exceed tolerance in either direction.
    """
    manifest = _validate_number(manifest_weight, "Manifest weight", allow_zero=False)
    scale = _validate_number(scale_weight, "Scale weight", allow_zero=False)
    tol = _validate_number(tolerance_pct, "Tolerance percentage", allow_zero=True)

    diff = scale - manifest
    pct = (diff / manifest) * 100
    allowed_diff = manifest * tol

    if abs(diff) <= allowed_diff:
        status = STATUS_WITHIN_TOLERANCE
    else:
        status = STATUS_REVIEW_REQUIRED

    return round(diff, 2), round(pct, 2), status


def audit_accessorial_charges(billed_charges, contract_schedule):
    """
    Audits billed surcharge fees against the contracted schedule.
    Flags overages and unlisted charges for human review.
    """
    billed = _normalize_schedule(billed_charges, "billed charges")
    contract = _normalize_schedule(contract_schedule, "contract schedule")

    total_review = 0.0
    line_items = []

    for code, b_amt in billed.items():
        if code not in contract:
            c_amt = None
            var_amt = b_amt
            status = STATUS_UNLISTED_SERVICE
        else:
            c_amt = contract[code]
            if b_amt > c_amt:
                var_amt = round(b_amt - c_amt, 2)
                status = STATUS_EXCEEDS_AGREED_RATE
            else:
                var_amt = 0.0
                status = STATUS_COMPLIANT

        total_review += var_amt
        line_items.append({
            "code": code,
            "billed": b_amt,
            "contract": c_amt,
            "variance": var_amt,
            "status": status,
        })

    return round(total_review, 2), line_items


def calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02):
    """
    Checks billed linehaul rate against quote.
    One-sided check: lower billed rates are compliant; overages trigger review.
    """
    quoted = _validate_number(quoted_rate, "Quoted rate", allow_zero=False)
    billed = _validate_number(billed_rate, "Billed rate", allow_zero=False)
    tol = _validate_number(tolerance_pct, "Tolerance percentage", allow_zero=True)

    diff = billed - quoted
    pct = (diff / quoted) * 100
    allowed_increase = quoted * tol

    if diff <= allowed_increase:
        status = STATUS_WITHIN_TOLERANCE
    else:
        status = STATUS_REVIEW_REQUIRED

    return {
        "quoted": round(quoted, 2),
        "billed": round(billed, 2),
        "diff": round(diff, 2),
        "variance_pct": round(pct, 2),
        "status": status,
    }


def main():
    po_number = "PO-2026-8841"
    manifest_wt = 4200
    scale_wt = 4550
    weight_tol = 0.05

    quoted_base = 450.00
    billed_base = 475.00
    base_tol = 0.02

    billed_accessorials = {
        "LIFTGATE": 85.00,
        "NOTIFY": 0.00,
        "DETENTION": 120.00,
    }
    contract_accessorials = {
        "liftgate": 65.00,
        "notify": 0.00,
    }

    w_diff, w_pct, w_status = verify_manifest_weight(manifest_wt, scale_wt, weight_tol)
    base_res = calculate_rate_variance(quoted_base, billed_base, base_tol)
    review_total, accessorial_log = audit_accessorial_charges(
        billed_accessorials, contract_accessorials
    )

    print("=" * 64)
    print(f"FREIGHT AUDIT REVIEW SUMMARY — {po_number}")
    print("=" * 64)

    print("\n[1] RECEIVING WEIGHT AUDIT")
    print(f"  Manifest Weight : {manifest_wt} lbs")
    print(f"  Scale Weight    : {scale_wt} lbs")
    print(f"  Variance        : {w_diff:+.2f} lbs ({w_pct:+.2f}%)")
    print(f"  Allowed Range   : ±{weight_tol * 100:.1f}%")
    print(f"  Status          : {w_status}")

    print("\n[2] BASE FREIGHT RATE AUDIT")
    print(f"  Quoted Rate     : ${base_res['quoted']:.2f}")
    print(f"  Billed Rate     : ${base_res['billed']:.2f}")
    print(f"  Variance        : ${base_res['diff']:+.2f} ({base_res['variance_pct']:+.2f}%)")
    print(f"  Allowed Ceiling : +{base_tol * 100:.1f}%")
    print(f"  Status          : {base_res['status']}")

    print("\n[3] ACCESSORIAL SURCHARGES AUDIT")
    print(f"  {'CODE':<14} {'BILLED':>10} {'CONTRACT':>10} {'REVIEW AMT':>12} {'STATUS'}")
    print("  " + "-" * 60)
    for item in accessorial_log:
        c_disp = f"${item['contract']:.2f}" if item['contract'] is not None else "UNLISTED"
        print(f"  {item['code']:<14} ${item['billed']:>9.2f} {c_disp:>10} ${item['variance']:>11.2f} {item['status']}")
    print("  " + "-" * 60)
    print(f"  Total Surcharge Review Amount: ${review_total:.2f}")

    print("\n" + "=" * 64)
    print("AUDIT FINDINGS DISCLAIMER:")
    print("This report highlights operational exceptions for human verification.")
    print("=" * 64)


if __name__ == "__main__":
    main()