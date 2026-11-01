"""
Freight Invoice & Receiving Review Assistant
CS50P Final Project
Author: Elliot Sandburg
"""

import math
from tabulate import tabulate

# Standardized Status Constants
STATUS_WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_COMPLIANT = "COMPLIANT"
STATUS_EXCEEDS_AGREED_RATE = "EXCEEDS_AGREED_RATE"
STATUS_UNLISTED_SERVICE = "UNLISTED_SERVICE"


def _validate_numeric(val: object, name: str, allow_zero: bool = False) -> float:
    """Helper to enforce finite, non-boolean numeric inputs."""
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(f"{name} must be a valid number, not boolean or string.")
    if not math.isfinite(val):
        raise ValueError(f"{name} must be a finite number (cannot be NaN or Inf).")
    if allow_zero:
        if val < 0:
            raise ValueError(f"{name} cannot be negative.")
    else:
        if val <= 0:
            raise ValueError(f"{name} must be a positive non-zero number.")
    return float(val)


def verify_manifest_weight(manifest_weight: float, scale_weight: float, tolerance_pct: float = 0.05) -> tuple[float, float, str]:
    """
    Compares declared manifest/BOL weight against recorded receiving dock scale weight.
    Returns: (weight_diff, variance_pct, status)
    """
    manifest_val = _validate_numeric(manifest_weight, "Manifest weight", allow_zero=False)
    scale_val = _validate_numeric(scale_weight, "Scale weight", allow_zero=False)
    tol_val = _validate_numeric(tolerance_pct, "Tolerance percentage", allow_zero=True)

    raw_diff = scale_val - manifest_val
    raw_variance_pct = (raw_diff / manifest_val) * 100.0

    # Direct threshold comparison with floating-point tolerance handling
    allowed_diff = manifest_val * tol_val
    if abs(raw_diff) <= allowed_diff or math.isclose(abs(raw_diff), allowed_diff, rel_tol=1e-9):
        status = STATUS_WITHIN_TOLERANCE
    else:
        status = STATUS_REVIEW_REQUIRED

    return round(raw_diff, 2), round(raw_variance_pct, 2), status


def audit_accessorial_charges(billed_charges: dict[str, float], contract_schedule: dict[str, float]) -> tuple[float, list[dict]]:
    """
    Audits line-item carrier surcharges against demonstration tariff fee schedules.
    Returns: (total_flagged_amount, itemized_audit_log)
    """
    if not isinstance(billed_charges, dict) or not isinstance(contract_schedule, dict):
        raise TypeError("Billed charges and contract schedule must be dictionaries.")

    # 1. Normalize and validate contract schedule upfront (detect empty codes and collisions)
    normalized_schedule: dict[str, float] = {}
    for code, amt in contract_schedule.items():
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Contract fee codes must be non-empty strings.")
        clean_code = code.strip().upper()
        if clean_code in normalized_schedule:
            raise ValueError(f"Normalization collision in contract schedule: '{clean_code}' defined multiple times.")
        validated_amt = _validate_numeric(amt, f"Contract fee for {clean_code}", allow_zero=True)
        normalized_schedule[clean_code] = validated_amt

    # 2. Normalize and validate billed charges upfront (detect empty codes and collisions)
    normalized_billed: dict[str, float] = {}
    for code, amt in billed_charges.items():
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Billed fee codes must be non-empty strings.")
        clean_code = code.strip().upper()
        if clean_code in normalized_billed:
            raise ValueError(f"Duplicate/colliding billed fee code: '{clean_code}' appears multiple times.")
        validated_amt = _validate_numeric(amt, f"Billed amount for {clean_code}", allow_zero=True)
        normalized_billed[clean_code] = validated_amt

    audit_log = []
    total_flagged_amount = 0.0

    # 3. Process normalized billing against schedule
    for clean_code, billed_val in normalized_billed.items():
        if clean_code not in normalized_schedule:
            status = STATUS_UNLISTED_SERVICE
            contract_val = None
            review_amount = billed_val
            total_flagged_amount += review_amount
        else:
            contract_val = normalized_schedule[clean_code]
            if billed_val > contract_val:
                status = STATUS_EXCEEDS_AGREED_RATE
                review_amount = billed_val - contract_val
                total_flagged_amount += review_amount
            else:
                status = STATUS_COMPLIANT
                review_amount = 0.0

        audit_log.append({
            "code": clean_code,
            "billed": round(billed_val, 2),
            "contract": round(contract_val, 2) if contract_val is not None else None,
            "variance": round(review_amount, 2),
            "status": status
        })

    return round(total_flagged_amount, 2), audit_log


def calculate_rate_variance(quoted_rate: float, billed_rate: float, tolerance_pct: float = 0.02) -> dict:
    """
    Compares contracted PO base freight quote to billed base freight rate.
    Flags ceiling increases exceeding the configured tolerance.
    Returns: dict with quoted, billed, diff, variance_pct, and status.
    """
    quoted_val = _validate_numeric(quoted_rate, "Quoted rate", allow_zero=False)
    billed_val = _validate_numeric(billed_rate, "Billed rate", allow_zero=False)
    tol_val = _validate_numeric(tolerance_pct, "Tolerance percentage", allow_zero=True)

    raw_diff = billed_val - quoted_val
    raw_variance_pct = (raw_diff / quoted_val) * 100.0

    allowed_increase = quoted_val * tol_val
    if raw_diff <= allowed_increase or math.isclose(raw_diff, allowed_increase, rel_tol=1e-9):
        status = STATUS_WITHIN_TOLERANCE
    else:
        status = STATUS_REVIEW_REQUIRED

    return {
        "quoted": round(quoted_val, 2),
        "billed": round(billed_val, 2),
        "diff": round(raw_diff, 2),
        "variance_pct": round(raw_variance_pct, 2),
        "status": status
    }


def main() -> None:
    # Demonstration shipment scenario using synthetic operational data
    scenario = {
        "po_number": "PO-99482-EUG",
        "invoice_number": "INV-788102",
        "carrier_name": "Example Freight Carrier",
        "manifest_weight": 4200.0,
        "scale_weight": 4550.0,
        "weight_tolerance": 0.05,
        "quoted_base_rate": 450.00,
        "billed_base_rate": 475.00,
        "rate_tolerance": 0.02,
        "contract_schedule": {
            "LIFTGATE": 65.00,
            "NOTIFY": 20.00,
            "LIMITED_ACCESS": 45.00
        },
        "billed_surcharges": {
            "LIFTGATE": 85.00,
            "NOTIFY": 20.00,
            "DETENTION": 120.00
        }
    }

    # 1. Execute Weight Audit
    wt_diff, wt_var_pct, wt_status = verify_manifest_weight(
        scenario["manifest_weight"],
        scenario["scale_weight"],
        scenario["weight_tolerance"]
    )

    # 2. Execute Surcharge Audit
    surcharge_total, surcharge_log = audit_accessorial_charges(
        scenario["billed_surcharges"],
        scenario["contract_schedule"]
    )

    # 3. Execute Rate Variance Audit
    rate_audit = calculate_rate_variance(
        scenario["quoted_base_rate"],
        scenario["billed_base_rate"],
        scenario["rate_tolerance"]
    )

    # Presentation Output
    print("=" * 80)
    print("           FREIGHT INVOICE & RECEIVING REVIEW ASSISTANT")
    print("=" * 80)
    print(f"PO Number: {scenario['po_number']:<28} Carrier: {scenario['carrier_name']}")
    print(f"Invoice #: {scenario['invoice_number']:<28} Mode: Synthetic Demonstration")
    print("-" * 80)

    print("\n[1] PHYSICAL CARGO WEIGHT VERIFICATION")
    weight_table = [[
        f"{scenario['manifest_weight']:,.2f}",
        f"{scenario['scale_weight']:,.2f}",
        f"{wt_diff:+,.2f}",
        f"{wt_var_pct:+.2f}%",
        wt_status
    ]]
    print(tabulate(
        weight_table,
        headers=["Manifest (lb)", "Scale (lb)", "Diff (lb)", "Variance %", "Audit Status"],
        tablefmt="grid",
        disable_numparse=True
    ))
    if wt_status == STATUS_REVIEW_REQUIRED:
        print(f"Notice: Scale weight variance ({wt_var_pct:+.2f}%) exceeds threshold ({scenario['weight_tolerance'] * 100:.2f}%).")

    print("\n[2] ACCESSORIAL SURCHARGE COMPLIANCE AUDIT")
    surcharge_table = []
    for item in surcharge_log:
        contract_display = f"${item['contract']:,.2f}" if item["contract"] is not None else "Not Listed"
        surcharge_table.append([
            item["code"],
            f"${item['billed']:,.2f}",
            contract_display,
            f"${item['variance']:,.2f}",
            item["status"]
        ])
    print(tabulate(
        surcharge_table,
        headers=["Service Code", "Billed", "Contracted", "Review Amount", "Finding Status"],
        tablefmt="grid",
        disable_numparse=True
    ))
    print(f"Total Surcharge Amount Requiring Review: ${surcharge_total:,.2f}")

    print("\n[3] BASE FREIGHT LINE-HAUL RATE VARIANCE")
    rate_table = [[
        f"${rate_audit['quoted']:,.2f}",
        f"${rate_audit['billed']:,.2f}",
        f"{rate_audit['diff']:+,.2f}",
        f"{rate_audit['variance_pct']:+.2f}%",
        rate_audit["status"]
    ]]
    print(tabulate(
        rate_table,
        headers=["Quoted Rate", "Billed Rate", "Diff ($)", "Variance %", "Audit Status"],
        tablefmt="grid",
        disable_numparse=True
    ))
    if rate_audit["status"] == STATUS_REVIEW_REQUIRED:
        print(f"Notice: Base rate variance ({rate_audit['variance_pct']:+.2f}%) exceeds threshold ({scenario['rate_tolerance'] * 100:.2f}%).")

    print("\n" + "=" * 80)
    print("RECONCILIATION SUMMARY:")
    print(f"- Weight Status:           {wt_status}")
    print(f"- Base Rate Status:        {rate_audit['status']} (${rate_audit['diff']:+,.2f})")
    print(f"- Surcharges for Review:   ${surcharge_total:,.2f}")
    print("-" * 80)
    print("* Disclaimer: Demonstration findings only. Results identify comparison differences")
    print("  for human coordinator review and do not establish contractual or legal liability.")
    print("=" * 80)


if __name__ == "__main__":
    main()