import math
from decimal import Decimal

# Operational review statuses
STATUS_WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_COMPLIANT = "COMPLIANT"
STATUS_EXCEEDS_AGREED_RATE = "EXCEEDS_AGREED_RATE"
STATUS_UNLISTED_SERVICE = "UNLISTED_SERVICE"


def _validate_numeric(val, name="Value", allow_zero=False):
    """
    Validates that a numeric argument is a finite integer or float.
    Rejects booleans, non-numeric types, non-finite values, and invalid signs.
    """
    if isinstance(val, bool):
        raise TypeError(f"{name} must be a number, not a boolean.")
    if not isinstance(val, (int, float)):
        raise TypeError(f"{name} must be an integer or float.")
    if not math.isfinite(val):
        raise ValueError(f"{name} must be a finite number.")
    if allow_zero:
        if val < 0:
            raise ValueError(f"{name} cannot be negative.")
    else:
        if val <= 0:
            raise ValueError(f"{name} must be strictly positive.")
    return val


def _normalize_and_validate_charges(charges_dict, dict_name="Charges"):
    """
    Validates accessorial fee schedules and billed charges.
    Normalizes codes (.strip().upper()) and detects normalized-key collisions.
    """
    if not isinstance(charges_dict, dict):
        raise TypeError(f"{dict_name} must be a dictionary.")

    normalized = {}
    for raw_code, amount in charges_dict.items():
        if not isinstance(raw_code, str):
            raise ValueError(f"Service code {raw_code!r} must be a string.")

        cleaned_code = raw_code.strip().upper()
        if not cleaned_code:
            raise ValueError(
                f"Service code in {dict_name} cannot be empty or whitespace-only."
            )

        if cleaned_code in normalized:
            raise ValueError(
                f"Duplicate service code collision detected: '{cleaned_code}' in {dict_name}."
            )

        _validate_numeric(amount, name=f"Amount for code '{cleaned_code}'", allow_zero=True)
        # Store as standard two-decimal cent representation
        normalized[cleaned_code] = round(float(amount), 2)

    return normalized


def verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05):
    """
    Audits physical scale weight against the billed manifest weight.
    Applies a two-sided inclusive tolerance threshold.
    Returns: (signed_difference, signed_percentage, status)
    """
    _validate_numeric(manifest_weight, "Manifest weight", allow_zero=False)
    _validate_numeric(scale_weight, "Scale weight", allow_zero=False)
    _validate_numeric(tolerance_pct, "Tolerance percentage", allow_zero=True)

    # Use Decimal to eliminate floating-point artifacts without widening business tolerance
    m_dec = Decimal(str(manifest_weight))
    s_dec = Decimal(str(scale_weight))
    tol_dec = Decimal(str(tolerance_pct))

    diff_dec = s_dec - m_dec
    pct_dec = (diff_dec / m_dec) * Decimal("100")
    allowed_diff = m_dec * tol_dec

    status = (
        STATUS_WITHIN_TOLERANCE
        if abs(diff_dec) <= allowed_diff
        else STATUS_REVIEW_REQUIRED
    )

    return float(round(diff_dec, 2)), float(round(pct_dec, 2)), status


def audit_accessorial_charges(billed_charges, contract_schedule):
    """
    Audits billed accessorial line items against the contracted fee schedule.
    Returns: (total_review_amount, list_of_line_item_findings)
    """
    billed = _normalize_and_validate_charges(billed_charges, "billed charges")
    contract = _normalize_and_validate_charges(contract_schedule, "contract schedule")

    total_review = Decimal("0.00")
    line_items = []

    for code, b_amt in billed.items():
        b_dec = Decimal(str(b_amt))
        if code not in contract:
            c_dec = None
            var_dec = b_dec
            status = STATUS_UNLISTED_SERVICE
        else:
            c_dec = Decimal(str(contract[code]))
            if b_dec > c_dec:
                var_dec = b_dec - c_dec
                status = STATUS_EXCEEDS_AGREED_RATE
            else:
                var_dec = Decimal("0.00")
                status = STATUS_COMPLIANT

        total_review += var_dec
        line_items.append({
            "code": code,
            "billed": float(b_dec),
            "contract": float(c_dec) if c_dec is not None else None,
            "variance": float(var_dec),
            "status": status,
        })

    return float(total_review), line_items


def calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02):
    """
    Audits the billed base linehaul rate against the agreed quote.
    Applies a one-sided ceiling check (lower billed rates are compliant).
    Returns: dict with quoted, billed, diff, variance_pct, and status.
    """
    _validate_numeric(quoted_rate, "Quoted rate", allow_zero=False)
    _validate_numeric(billed_rate, "Billed rate", allow_zero=False)
    _validate_numeric(tolerance_pct, "Tolerance percentage", allow_zero=True)

    q_dec = Decimal(str(quoted_rate))
    b_dec = Decimal(str(billed_rate))
    tol_dec = Decimal(str(tolerance_pct))

    diff_dec = b_dec - q_dec
    pct_dec = (diff_dec / q_dec) * Decimal("100")
    allowed_increase = q_dec * tol_dec

    status = (
        STATUS_WITHIN_TOLERANCE
        if diff_dec <= allowed_increase
        else STATUS_REVIEW_REQUIRED
    )

    return {
        "quoted": float(round(q_dec, 2)),
        "billed": float(round(b_dec, 2)),
        "diff": float(round(diff_dec, 2)),
        "variance_pct": float(round(pct_dec, 2)),
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
    print(f"  Threshold       : ±{weight_tol * 100:.2f}% (unrounded comparison)")
    print(f"  Status          : {w_status}")
    if w_status == STATUS_REVIEW_REQUIRED:
        print(f"  Notice          : Absolute weight variance exceeds ±{weight_tol * 100:.2f}% tolerance.")

    print("\n[2] BASE FREIGHT RATE AUDIT")
    print(f"  Quoted Rate     : ${base_res['quoted']:.2f}")
    print(f"  Billed Rate     : ${base_res['billed']:.2f}")
    print(f"  Variance        : ${base_res['diff']:+.2f} ({base_res['variance_pct']:+.2f}%)")
    print(f"  Allowed Ceiling : +{base_tol * 100:.2f}%")
    print(f"  Status          : {base_res['status']}")
    if base_res['status'] == STATUS_REVIEW_REQUIRED:
        print(f"  Notice          : Billed rate exceeds quoted ceiling by ${base_res['diff'] - (base_res['quoted'] * base_tol):.2f}.")

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
    print("This report highlights discrepancies requiring human operational review.")
    print("It does not constitute a legal determination of contractual liability.")
    print("=" * 64)
    return None


if __name__ == "__main__":
    main()