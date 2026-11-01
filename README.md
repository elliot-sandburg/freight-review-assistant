# Freight Invoice & Receiving Review Assistant

#### Video Demo: [INSERT YOUTUBE UNLISTED LINK HERE]

## Description

The **Freight Invoice & Receiving Review Assistant** is an automated pre-payment auditing tool designed to assist logistics and receiving teams. In freight transportation, invoices frequently deviate from quoted terms due to scale weight discrepancies, unlisted accessorial surcharges (e.g., liftgate fees, detention), or unapproved linehaul rate increases. 

This program programmatically reconciles receiving weights, base linehaul rates, and accessorial fees against contracted schedules and initial quotes. It produces an itemized operational review summary identifying billing exceptions that require human operational verification prior to invoice approval.

---

## Architecture & Core Functions

The core business logic is implemented in `project.py` across three primary audit functions and an execution entrypoint:

1. `verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05)`
   * Reconciles physical scale readings against billed bill-of-lading (BOL) manifest weights.
   * Enforces a two-sided inclusive tolerance percentage (default: ±5.0%).
   * Evaluates boundary thresholds via decimal representation to eliminate binary floating-point representation anomalies without expanding business tolerance windows.
   * Returns: `(signed_difference, signed_percentage, status)`

2. `audit_accessorial_charges(billed_charges, contract_schedule)`
   * Audits billed surcharge line items against an agreed contract tariff schedule.
   * Normalizes service codes (stripping whitespace and converting to uppercase) and flags collision errors if duplicate variations of the same code exist within a schedule.
   * Reconciles unlisted services (assigning `contract=None` and marking the entire charge for review) and rate overages.
   * Uses two-decimal cent precision to guarantee that individual line-item review variances sum identically to the total review amount.
   * Returns: `(total_review_amount, list_of_line_item_findings)`

3. `calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02)`
   * Compares the final billed linehaul freight charge against the initial quote.
   * Implements a one-sided ceiling check: billed rates that are less than or equal to the allowed quote ceiling are marked `WITHIN_TOLERANCE`.
   * Returns a structured dictionary containing quoted, billed, variance, percentage, and review status.

4. `main()`
   * Orchestrates the synthetic end-to-end audit scenario for purchase order `PO-2026-8841`.
   * Formats and prints an itemized operational summary table along with a legal review disclaimer.

---

## Design Decisions & Numerical Integrity

* **Strict Boundary Classification:** To prevent standard IEEE 754 floating-point representation artifacts (e.g., $1.1 - 1.0 = 0.10000000000000009$) without using wide relative tolerances that permit genuine overages, threshold calculations convert inputs to Python's built-in `Decimal` during comparison.
* **One-Sided Base-Rate Ceiling:** Lower base rates are beneficial to the shipper and are treated as compliant; only positive variances exceeding the tolerance trigger review.
* **Defensive Input Validation:** All inputs reject boolean values (`True`/`False`), non-finite floats (`NaN`, `±Inf`), and negative amounts where forbidden.
* **Human Operational Review:** Audit statuses (`REVIEW_REQUIRED`, `EXCEEDS_AGREED_RATE`, `UNLISTED_SERVICE`) highlight operational discrepancies; they do not constitute legal determinations of contractual liability.

---

## Installation & Execution

### Prerequisites
* Python 3.10+
* Virtual environment (recommended)

### Setup & Run

1. Clone the repository and navigate to the root directory:
```bash
git clone https://github.com/elliot-sandburg/freight-review-assistant.git
cd freight-review-assistant