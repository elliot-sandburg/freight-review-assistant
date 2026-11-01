# Freight Invoice & Receiving Review Assistant

#### Video Demo: [INSERT YOUTUBE UNLISTED LINK HERE]

## Project Overview
In commercial distribution and transportation operations, freight billing differences frequently create operational and accounting delays. Shipping coordinators must regularly review carrier invoices against contracted purchase order quotes and warehouse scale records to identify variances before invoices are approved for payment.

The **Freight Invoice & Receiving Review Assistant** is an educational command-line application written in Python. It models cross-document reconciliation by comparing a synthetic carrier freight bill against two baseline reference records:
1. **The Contract / Purchase Order Quote:** Contracted line-haul rates, tariff accessorial schedules, and configured variance tolerances.
2. **The Receiving Scale Log:** Physical gross scale weight recorded upon delivery at the destination warehouse.

The software calculates variances, applies unrounded mathematical boundary classifications, and generates an organized review report using objective, neutral findings.

## Project Structure & Files

* `project.py`: Contains `main()` and three standalone top-level audit functions. It coordinates sample scenario data, executes reconciliation logic, and displays formatted review tables using `tabulate`.
* `test_project.py`: A unit testing suite executed with `pytest`. It verifies boundary thresholds, normalization logic, return schemas, collision handling, and exception handling across all core functions.
* `requirements.txt`: Defines direct external pip dependencies (`tabulate` and `pytest`).
* `README.md`: Comprehensive documentation detailing the software's architecture, design decisions, and usage.

## Core Functions & Architecture

`project.py` is architected around three standalone functions defined at the top level:

### 1. `verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05)`
Compares declared Bill of Lading (BOL) weight against the recorded receiving dock scale weight. It calculates the signed difference and percentage variance. The function classifies the result using floating-point math with epsilon tolerance handling before rounding returned values:
* Returns `WITHIN_TOLERANCE` if the absolute variance is within the configured threshold.
* Returns `REVIEW_REQUIRED` if the absolute variance exceeds the threshold.
Raises `TypeError` for booleans or non-numbers, and `ValueError` for non-positive weights, negative tolerances, or non-finite numbers (`NaN`/`Inf`).

### 2. `audit_accessorial_charges(billed_charges, contract_schedule)`
Audits line-item carrier accessorial surcharges against the demonstration tariff schedule. 
* Validates and normalizes all fee codes in both dictionaries upfront (case-insensitive, whitespace-stripped).
* Rejects empty codes or normalization collisions within either dictionary.
* Flags fees not present in the contract schedule as `UNLISTED_SERVICE` (setting agreed contract value to `None`).
* Flags fees exceeding the contracted rate as `EXCEEDS_AGREED_RATE` and tallies the dollar delta.
* Flags fees at or below contracted rate as `COMPLIANT`.
Raises `ValueError` for negative dollar amounts, non-finite values, empty code strings, or key collisions. Raises `TypeError` for non-dictionary inputs.

### 3. `calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02)`
Compares contracted PO base freight rates against billed base freight rates (excluding accessorials). It flags ceiling increases exceeding the configured tolerance:
* Returns `WITHIN_TOLERANCE` if billed rate drift is $\le$ tolerance threshold.
* Returns `REVIEW_REQUIRED` if billed rate drift exceeds tolerance threshold.
Raises `TypeError` for booleans, and `ValueError` if rates are $\le 0$, tolerance is negative, or values are non-finite.

## Design Rationale

* **Direct Threshold Comparison & Epsilon Precision:** Mathematical comparisons are made against unrounded float values using direct allowable delta checks and `math.isclose()` relative tolerances. This prevents floating-point decimal artifacts (such as 1.1 - 1.0 = 0.10000000000000009) while ensuring actual boundary excursions (e.g., 5.0025%) trigger review.
* **Two-Sided Upfront Normalization & Collision Detection:** Fee codes in both dictionaries are validated, trimmed, and uppercased prior to evaluation. If a dictionary contains colliding keys (e.g., `"liftgate"` and `" LIFTGATE "`), the application raises a `ValueError` rather than silently overwriting data.
* **Separation of Variance Pools:** Base line-haul rate variances and accessorial surcharge overages are kept distinct. A lower base freight rate is not permitted to net against or obscure unlisted accessorial fees.
* **Neutral Findings Language:** The application reports factual comparison statuses (`REVIEW_REQUIRED`, `UNLISTED_SERVICE`) rather than making allegations of misconduct, determining legal liability, or issuing payment authorizations.

## Demonstration Assumptions & Limitations

* **Synthetic Data:** All demonstration records (PO, invoice, weights, and rates) are synthetic and do not represent actual commercial carriers or transactions.
* **Measurement Comparability:** Declared and measured weights are assumed to share identical units (lbs) and measurement baselines.
* **Currency Uniformity:** All monetary values are assumed to be in US Dollars (USD).
* **Aggregated Surcharges:** Billed accessorial fees are assumed to be pre-aggregated per service code.

## Installation & Execution

1. Activate your virtual environment and install dependencies:
   python -m pip install -r requirements.txt

2. Run the application:
   python project.py

3. Run the unit test suite:
   python -m pytest test_project.py -v