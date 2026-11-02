# Freight Invoice & Receiving Review Assistant
#### Video Demo:  <YOUR_YOUTUBE_UNLISTED_LINK_HERE>
#### Description:

### Why I Built This
Freight bills often don't match what was agreed to. A carrier might bill for a different weight than the warehouse scale recorded, tack on a liftgate or residential delivery fee nobody approved, or quote a higher linehaul rate than the one on the purchase order. Catching these by hand means flipping between the bill of lading, scale tickets, and the invoice, and it's easy to miss something. This project is a small Python tool that does that comparison for me and produces a report listing what needs a human to look at before anyone pays.

### Project Files

#### `project.py`
This is the main program. It has four functions.

1. `verify_manifest_weight(manifest_weight, scale_weight, tolerance_pct=0.05)` compares the weight on the manifest to the warehouse scale reading. I check both directions, since a shortage could mean lost freight and an overage could mean the carrier is padding the bill. It returns the weight difference, the percentage variance, and a status of `MATCH`, `WITHIN_TOLERANCE`, or `REVIEW_REQUIRED`. It raises an error if any weight or tolerance is negative or not a number.

2. `audit_accessorial_charges(billed_charges, contract_schedule)` checks surcharges against the contract. Service codes get stripped and uppercased first so that `" ldg "` and `"LDG"` count as the same thing. Any charge that isn't in the contract gets flagged in full, and any charge above the contracted cap gets flagged for the amount over. The function returns the total dollars needing review along with a line-by-line list. It also raises an error if the contract has duplicate codes, since that would make the lookup ambiguous.

3. `calculate_rate_variance(quoted_rate, billed_rate, tolerance_pct=0.02)` compares the billed linehaul rate to the quote. This one only cares about going over. A lower rate is a discount, so it passes. A higher rate passes only if it's inside the 2% tolerance. The function returns a dictionary with the quote, the billed amount, the dollar difference, the percentage difference, and the status.

4. `main()` runs a demo on a sample shipment, `PO-2026-8841`. It goes through the scale weights, linehaul amount, and accessorial fees, then prints a readable report with the items that need review.

#### `test_project.py`
These are `pytest` tests for the three audit functions. Each function has its own test. They cover exact matches, small variances that should pass, overages and shortages that should get flagged, and bad inputs that should raise errors. The accessorial test also checks that casing and extra spaces get normalized and that duplicate codes are caught.

#### `requirements.txt`
This only lists `pytest`, which is the one thing you need to run the tests.

### Design Choices
The audit functions don't print anything or ask for input. They take values in and return tuples, dictionaries, and lists. I did this so the logic could be tested without mocking the terminal, and so the printing could change later without touching the math.

Weight and rate use different rules on purpose. For weight, an underage and an overage are both problems, so the check is two-sided. For rates, paying less than the quote is good for the shipper, so only going over the quote should trigger a hold.

When something is wrong with the inputs, like a negative weight or a string where a number should be, the functions raise an error instead of quietly returning a default. A default would hide the problem, and in a billing check a hidden problem is the worst outcome.

### Running It
```bash
pip install -r requirements.txt
pytest
```
To see the sample report, run `python project.py`.
