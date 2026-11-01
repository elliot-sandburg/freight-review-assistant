# Freight Invoice & Receiving Review Assistant

#### Video Demo: [INSERT YOUTUBE UNLISTED LINK HERE]

## Description

The **Freight Invoice & Receiving Review Assistant** is an automated pre-payment audit tool written in Python. In commercial freight transportation, shipping invoices frequently differ from original quotes and purchase orders due to receiving weight discrepancies, unlisted accessorial surcharges (such as liftgate or detention fees), and unapproved linehaul rate increases.

This program reconciles delivery scale weights, base freight rates, and accessorial fees against contracted tariffs and original quotes. It generates an itemized audit summary highlighting billing discrepancies that require human operational review before payment is approved.

---

## Project Structure & Files

* **`project.py`**: Contains the core audit logic, data validation, and command-line demonstration report.
* **`test_project.py`**: Implements automated unit test suites using `pytest` to test the three required functions.
* **`requirements.txt`**: Lists the project's external package dependencies (`pytest`).
* **`README.md`**: Provides documentation, architectural decisions, and usage instructions.

---

## Core Functions

1. `verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05)`
   * Reconciles physical delivery scale weights against billed manifest weights.
   * Enforces a two-sided tolerance threshold (default ±5.0%) to flag both overages and significant underages.
   * Returns: `(difference, percentage, status)`

2. `audit_accessorial_charges(billed_charges, contract_schedule)`
   * Audits billed surcharge line items against an agreed contract tariff schedule.
   * Normalizes service codes by stripping whitespace and converting to uppercase, and raises an error if duplicate variations of a code exist.
   * Flags unlisted services (marking the entire amount for review) and rate overages.
   * Returns: `(total_review_amount, line_items_list)`

3. `calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02)`
   * Audits the billed linehaul rate against the agreed quote.
   * Implements a one-sided ceiling check: billed rates lower than the quote are compliant, while increases exceeding the tolerance percentage trigger review.
   * Returns: a dictionary containing quoted, billed, variance, percentage, and review status.

4. `main()`
   * Runs an end-to-end demonstration using sample freight data for purchase order `PO-2026-8841`.
   * Formats and prints an itemized summary table with operational review notices.

---

## Design Decisions

* **One-Sided Base-Rate Ceiling:** Base freight rates enforce a ceiling. Lower billed rates benefit the shipper and are treated as compliant.
* **Two-Sided Weight Tolerance:** Weight discrepancies in either direction (heavier or lighter than manifest) indicate potential receiving errors or missing freight.
* **Defensive Validation:** Inputs are validated to prevent invalid types, negative amounts, and zero values where forbidden.
* **Human-in-the-Loop:** Audit statuses (`REVIEW_REQUIRED`, `EXCEEDS_AGREED_RATE`, `UNLISTED_SERVICE`) highlight operational discrepancies for human review; they do not constitute legal determinations of liability.

---

## Installation & Execution

1. Activate your virtual environment and install dependencies:
```bash
pip install -r requirements.txt