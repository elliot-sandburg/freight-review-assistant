# Freight Invoice & Receiving Review Assistant

#### Video Demo: https://www.youtube.com/watch?v=7X8D1ITSqHw

## Description

Freight invoices don't always match what was agreed to. The weight on the bill might not match what the dock scale read, a liftgate or detention fee might show up that nobody approved, or the linehaul rate might creep above the quote. This tool checks those invoices before anyone pays them. It compares scale weights, base rates, and accessorial charges against the contracted tariff and the original quote, then produces an itemized summary of anything that needs a person to look at it.

---

## Project Structure

- **`project.py`**: The audit logic, input validation, and a command-line demo report.
- **`test_project.py`**: `pytest` unit tests for the three core functions.
- **`requirements.txt`**: The external dependencies (just `pytest`).
- **`README.md`**: This file.

---

## Core Functions

1. **`verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05)`**
   Compares the scale weight with the billed manifest weight. The check runs in both directions, with a default tolerance of ±5%, so it catches heavy overages and suspicious underages alike. Returns `(difference, percentage, status)`.

2. **`audit_accessorial_charges(billed_charges, contract_schedule)`**
   Checks each billed surcharge against the agreed tariff. Service codes are trimmed and uppercased before comparison, and the function raises an error if the same code shows up in more than one form. Any service not on the schedule is flagged for review in full, and any charge above its contracted rate is flagged for the overage. Returns `(total_review_amount, line_items_list)`.

3. **`calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02)`**
   Checks the billed linehaul rate against the quote. This is a one-sided ceiling: a lower billed rate is fine since it favors the shipper, but an increase beyond the tolerance gets flagged. Returns a dictionary with the quoted rate, billed rate, variance, percentage, and review status.

4. **`main()`**
   Runs an end-to-end demo using sample data for purchase order `PO-2026-8841` and prints an itemized table with review notices.

---

## Design Decisions

- **One-sided rate ceiling:** A billed rate below the quote is treated as compliant, since the shipper benefits.
- **Two-sided weight tolerance:** A shipment that weighs more or less than the manifest can both point to a receiving error or missing freight, so both directions get checked.
- **Defensive validation:** Bad inputs are rejected up front: wrong types, negative amounts, and zeros where they don't make sense.
- **Human in the loop:** The statuses (`REVIEW_REQUIRED`, `EXCEEDS_AGREED_RATE`, `UNLISTED_SERVICE`) mark items for a person to review. They aren't legal findings about who owes what.

---

## Installation & Usage

1. Install the dependencies:

```bash
pip install -r requirements.txt
```