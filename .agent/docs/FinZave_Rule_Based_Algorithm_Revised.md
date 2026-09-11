# FinZave — Rule-Based Financial Analysis Algorithm
## Revised and Implementation-Ready Specification

## 1. Purpose

FinZave uses a **Rule-Based Financial Analysis Algorithm** as its financial intelligence layer.

The engine converts a user's recorded financial data into:

1. Financial metrics
2. Period comparisons
3. Spending behaviour observations
4. Rule evaluations
5. Explainable insights
6. Prioritized recommendations

The algorithm is deterministic and does not use Machine Learning, LLMs, market prediction, or AI recommendation models.

### Core pipeline

```text
Financial Data
      ↓
Validation
      ↓
Metric Calculation
      ↓
Period Comparison
      ↓
Behaviour Analysis
      ↓
Rule Evaluation
      ↓
Insight Generation
      ↓
Deduplication & Prioritization
      ↓
Persist Analysis
      ↓
Cache
      ↓
Dashboard / Analysis
```

---

# 2. Design Principles

The rule engine follows these principles:

### 2.1 Deterministic

The same financial input must produce the same result.

### 2.2 Explainable

Every insight must identify the rule that generated it and the numerical evidence behind it.

### 2.3 User-specific

Where possible, the system compares the user's current behaviour with the user's own historical behaviour rather than relying only on population-wide assumptions.

### 2.4 Conservative

The engine should not make claims that cannot be supported by the available data.

### 2.5 Testable

Every rule must have explicit inputs, conditions, thresholds, and expected outputs.

### 2.6 Centralized thresholds

All configurable thresholds must be defined in one configuration area.

---

# 3. Input Data

The analysis engine consumes the following data.

## 3.1 Income

Each income record contains:

```text
user_id
amount
income_type
date
```

Income types:

```text
FIXED
VARIABLE
```

Examples of fixed income:

- Salary
- Regular pension
- Recurring rental income

Examples of variable income:

- Freelancing
- Bonus
- Commission
- Irregular business income

---

## 3.2 Expenses

Each expense record contains:

```text
user_id
amount
category
description
date
```

The category is stored directly on the expense record.

There is no separate category-management module.

---

# 4. Basic Financial Metrics

For each analysis period:

## 4.1 Total Income

```text
Total Income = Fixed Income + Variable Income
```

## 4.2 Total Expenses

```text
Total Expenses = Σ valid expense amounts
```

## 4.3 Savings

```text
Savings = Total Income - Total Expenses
```

## 4.4 Savings Rate

```text
Savings Rate =
(Savings / Total Income) × 100
```

If:

```text
Total Income = 0
```

then the engine must not perform the division.

The metric should be represented as unavailable/undefined for that period rather than inventing a percentage.

---

# 5. Period Comparison

The engine compares the current period with a previous period when sufficient data exists.

## 5.1 Percentage Change

```text
Change % =
((Current - Previous) / Previous) × 100
```

### Zero-previous-value guard

If:

```text
Previous = 0
```

the percentage change must **not** be calculated.

Instead:

```text
Comparison Status = INSUFFICIENT_DATA
```

This applies to income, expenses, savings, category values, and any other metric using the percentage-change formula.

This prevents division-by-zero errors and misleading percentages for a new user or a period following a zero-value period.

---

# 6. Trend Classification

For a valid previous value, period-to-period change is classified using:

```text
Change < -5%       → DECREASING
-5% to +5%         → STABLE
Change > +5%       → INCREASING
```

The threshold is:

```text
TREND_CHANGE_PERCENTAGE = 5%
```

Trend classification and consecutive-period detection are separate mechanisms.

### Classification answers:

> "Did this period increase, decrease, or remain stable?"

### Consecutive-run detection answers:

> "Has this pattern continued for several periods?"

---

# 7. Consecutive Trend Detection

For rules that require a persistent trend, FinZave uses:

```text
CONSECUTIVE_PERIODS_FOR_TREND = 3
```

Therefore, an increasing-expense insight requires three consecutive comparable periods showing an increasing pattern.

Example:

```text
January   → baseline
February  → increasing
March     → increasing
April     → increasing
```

Result:

```text
Increasing Expense Trend = TRUE
```

If there are fewer than the required comparable periods:

```text
MIN_PERIODS_FOR_COMPARISON = 2
```

the engine should return:

```text
INSUFFICIENT_DATA
```

rather than making a trend claim.

---

# 8. Rule Configuration

The initial project-defined thresholds are:

| Constant | Value | Used By |
|---|---:|---|
| `LOW_SAVINGS_RATE` | 20% | RB-03 |
| `POSITIVE_SAVINGS_RATE` | 20% | RB-08 |
| `TREND_CHANGE_PERCENTAGE` | 5% | Trend classification |
| `HIGH_CATEGORY_PERCENTAGE` | 30% | RB-02 supporting threshold |
| `CATEGORY_DEVIATION_FACTOR` | 1.5× | RB-02 |
| `DISCRETIONARY_SPENDING_THRESHOLD` | 30% | RB-06 |
| `CONSECUTIVE_PERIODS_FOR_TREND` | 3 | RB-01, RB-04 |
| `MIN_PERIODS_FOR_COMPARISON` | 2 | Trend/comparison rules |
| `SIP_HIGH_COMMITMENT_RATIO` | 75% | SIP insight |
| `EMI_HIGH_COMMITMENT_RATIO` | 75% | EMI insight |

These are **application-defined analytical thresholds**, not universal financial standards or professional financial advice.

---

# 9. Rule RB-01 — Increasing Expenses

## Objective

Detect whether the user's expenses have been increasing consistently.

## Inputs

```text
Monthly expense totals
Trend classification
```

## Condition

```text
IF
    at least 3 comparable consecutive periods exist
AND
    each consecutive period is classified as INCREASING
THEN
    RB-01 fires
```

The three periods must have valid comparisons.

## Example

```text
January   ₹20,000
February  ₹23,000
March     ₹27,000
```

```text
January → February = +15%
February → March  ≈ +17.39%
```

With the required consecutive sequence established across the available periods, the rule can identify an increasing trend.

## Output

```text
Rule ID: RB-01
Group: EXPENSE_PRESSURE
Severity: WARNING
```

Example message:

> Your expenses have been increasing consistently over recent periods.

---

# 10. Rule RB-02 — Personalised Category Spending Deviation

## Problem with simple category thresholds

A rule such as:

```text
IF Food > 30%
THEN highlight Food
```

is not sufficiently useful by itself.

Rent, for example, may naturally be the largest category for many users. Repeatedly reporting "Rent is your highest category" does not necessarily provide a useful or changing insight.

## Improved approach

RB-02 primarily compares the user's current category spending with their own historical category behaviour.

For a category:

```text
Current Category Share =
Current Category Expense / Current Total Expense × 100
```

Calculate the user's historical average category share:

```text
Historical Average Category Share =
Average of previous comparable period shares
```

Then calculate:

```text
Category Deviation Ratio =
Current Category Share / Historical Average Category Share
```

## Condition

RB-02 fires when:

```text
Current Category Share >= HIGH_CATEGORY_PERCENTAGE
AND
Current Category Share >=
Historical Average Category Share × CATEGORY_DEVIATION_FACTOR
```

where:

```text
HIGH_CATEGORY_PERCENTAGE = 30%
CATEGORY_DEVIATION_FACTOR = 1.5
```

This means the category must both be significant in the current period and unusually large relative to the user's own history.

## Example

Historical Food share:

```text
January   = 24%
February  = 26%
Historical average = 25%
```

Current month:

```text
Food = 38%
```

Deviation:

```text
38 / 25 = 1.52×
```

Because:

```text
38% >= 30%
AND
1.52× >= 1.5×
```

RB-02 fires.

## Insight

> Food represents 38% of your spending this month, compared with your usual average of about 25%.

This is more personalized and actionable than simply reporting the largest category.

## Insufficient history

If historical category data is unavailable or insufficient:

```text
RB-02 = INSUFFICIENT_DATA
```

The engine should not manufacture a historical comparison.

---

# 11. Rule RB-03 — Low Savings Rate

## Objective

Identify a relatively low savings rate.

```text
LOW_SAVINGS_RATE = 20%
```

## Condition

```text
IF
    Total Income > 0
AND
    Savings Rate < 20%
THEN
    RB-03 fires
```

## Example

```text
Income = ₹50,000
Expenses = ₹42,000

Savings = ₹8,000

Savings Rate =
8,000 / 50,000 × 100
= 16%
```

Result:

```text
16% < 20%
```

RB-03 fires.

## Insight

> Your current savings rate is below the FinZave analysis threshold.

The threshold is a project-defined analytical threshold and should not be presented as a universal financial rule.

---

# 12. Rule RB-04 — Declining Savings

## Objective

Identify a persistent decline in savings.

## Condition

```text
IF
    at least 3 comparable periods exist
AND
    savings show a decreasing pattern
    across the required consecutive periods
THEN
    RB-04 fires
```

Example:

```text
January   ₹15,000
February  ₹12,000
March      ₹9,000
```

## Insight

> Your savings have been declining over recent periods.

---

# 13. Rule RB-05 — Expenses Growing Faster Than Income

## Objective

Identify cases where expenses are increasing faster than income.

## Important sign guard

The rule must require:

```text
Expense Growth > 0
```

Without this condition, a decrease in income can incorrectly cause the rule to fire.

## Condition

```text
IF
    income comparison is valid
AND
    expense comparison is valid
AND
    Expense Growth > 0
AND
    Expense Growth > Income Growth
THEN
    RB-05 fires
```

## Correct example

```text
Income:
₹50,000 → ₹52,000
Growth = +4%

Expenses:
₹30,000 → ₹34,000
Growth ≈ +13.33%
```

Since:

```text
Expense Growth > 0
AND
13.33% > 4%
```

RB-05 fires.

## Insight

> Your expenses rose by 13.3% while your income rose by 4.0%.

## Important non-firing example

```text
Income:
₹50,000 → ₹40,000
Growth = -20%

Expenses:
₹30,000 → ₹28,500
Growth = -5%
```

Although:

```text
-5% > -20%
```

RB-05 **does not fire**, because:

```text
Expense Growth = -5%
```

and the rule requires:

```text
Expense Growth > 0
```

The correct interpretation is that expenses decreased while income declined.

This situation can be reported separately as an informational observation:

> Your income declined while expenses also decreased.

A separate rule is not required unless this becomes a future project requirement.

---

# 14. Rule RB-06 — High Discretionary Spending

## Objective

Identify when discretionary categories represent a significant share of spending.

Example discretionary categories:

```text
Entertainment
Shopping
Dining
Travel
Subscriptions
```

The classification of categories should be maintained centrally.

## Formula

```text
Discretionary Spending % =
Discretionary Expenses / Total Expenses × 100
```

## Condition

```text
IF
    Discretionary Spending % >= 30%
THEN
    RB-06 fires
```

## Insight

> A significant portion of your expenses is going toward discretionary categories.

The rule identifies a spending pattern; it does not label the user's spending as irresponsible.

---

# 15. Rule RB-07 — Historical Category Overspending

RB-07 is redefined so that it does **not** depend on a separate budget table.

The rule uses the user's own historical category behaviour.

## Objective

Identify an unusually high current category share relative to the user's normal pattern.

The same historical evidence used by RB-02 can support this analysis.

A category is considered unusually elevated when:

```text
Current Category Share >=
Historical Average Category Share × CATEGORY_DEVIATION_FACTOR
```

and sufficient historical data exists.

## Relationship with RB-02

RB-02 emphasizes a category that is both:

```text
Significant
+
Unusually high
```

RB-07 can represent the broader historical-deviation finding if the implementation chooses to expose it separately.

To prevent duplicate messages, RB-02 and RB-07 belong to the same deduplication group:

```text
SPENDING_CONCENTRATION
```

The implementation should not show two messages describing exactly the same category deviation.

---

# 16. Rule RB-08 — Positive Savings Pattern

## Objective

Provide balanced feedback when savings are positive.

```text
POSITIVE_SAVINGS_RATE = 20%
```

## Condition

```text
IF
    Total Income > 0
AND
    Savings Rate >= 20%
AND
    savings are stable or increasing
THEN
    RB-08 fires
```

Because:

```text
LOW_SAVINGS_RATE = 20%
POSITIVE_SAVINGS_RATE = 20%
```

the two rules are mutually exclusive at the boundary.

Example:

```text
Savings Rate = 20%
```

RB-03:

```text
20% < 20%
FALSE
```

RB-08:

```text
20% >= 20%
TRUE
```

Therefore the system cannot simultaneously generate a low-savings warning and a positive-savings insight for the same period.

## Insight

> Your savings pattern is currently positive based on the FinZave analysis threshold.

---

# 17. Rule RB-09 — Income Profile

## Objective

Use FinZave's fixed/variable income distinction to understand income composition.

## Formulas

```text
Fixed Income % =
Fixed Income / Total Income × 100
```

```text
Variable Income % =
Variable Income / Total Income × 100
```

## Example

```text
Fixed Income = ₹45,000
Variable Income = ₹10,000
Total Income = ₹55,000
```

Therefore:

```text
Fixed Income % ≈ 81.82%
Variable Income % ≈ 18.18%
```

## Insight

> Most of your recorded income comes from fixed sources.

If variable income forms a significant share:

> A significant portion of your recorded income comes from variable sources.

RB-09 is an informational rule and does not classify variable income as inherently good or bad.

---

# 18. No Duplicate Expense-Ratio Rule

An earlier version contained:

```text
RB-10 — Financial Expense Pressure
```

based on:

```text
Expense Ratio =
Expenses / Income × 100
```

This rule has been **removed**.

The reason is mathematical equivalence:

```text
Savings = Income - Expenses

Savings Rate =
(Income - Expenses) / Income × 100

Savings Rate =
100 - Expense Ratio
```

Therefore:

```text
Savings Rate < 20%
```

and:

```text
Expense Ratio > 80%
```

are exactly the same condition.

Keeping both would produce duplicate insights and artificially inflate the number of rules.

**RB-03 is retained. RB-10 is deleted.**

---

# 19. Optional Distinct Fixed-Income Pressure Signal

The fixed/variable distinction can support a genuinely different future rule.

For example:

```text
IF
    Total Expenses > Fixed Income
THEN
    identify that expenses exceed stable recorded income
```

This is different from savings rate because it compares expenses specifically against **fixed income**, not total income.

Possible message:

> Your current expenses exceed your recorded fixed income and therefore depend partly on variable income.

This is a potential enhancement to the current rule set and should only be implemented if it is formally accepted into the project scope.

---

# 20. SIP Affordability Analysis

The SIP calculator and SIP financial insight are separate operations.

## 20.1 SIP Calculation

Inputs:

```text
Monthly SIP Amount
Expected Annual Return
Investment Duration
```

Outputs:

```text
Total Investment
Estimated Returns
Estimated Future Value
```

The expected return is supplied by the user.

FinZave does not predict market returns.

---

## 20.2 Stable Savings Basis

A single unusual month should not determine SIP affordability.

Therefore:

```text
Average Monthly Savings =
Average of valid monthly savings
over the trailing 3 months
```

The engine should use the trailing three-month average when sufficient data exists.

If fewer than three valid months are available:

```text
SIP Affordability =
INSUFFICIENT_DATA
```

unless the UI explicitly chooses a less strict fallback and clearly labels it.

---

## 20.3 SIP Rules

```text
IF
    SIP Amount > Average Monthly Savings
THEN
    MAY_NOT_BE_PRACTICAL
```

Otherwise:

```text
IF
    SIP Amount > 75% of Average Monthly Savings
THEN
    HIGH_COMMITMENT
```

Otherwise:

```text
POTENTIALLY_MANAGEABLE
```

Example:

```text
Average Monthly Savings = ₹12,000
SIP = ₹10,000

SIP / Savings = 83.33%
```

Result:

```text
HIGH_COMMITMENT
```

The UI should state:

> Based on your average savings over the last 3 months, this SIP represents a high monthly commitment.

This is an affordability observation, not investment advice.

---

# 21. EMI Affordability Analysis

## 21.1 EMI Calculation

Inputs:

```text
Loan Amount
Interest Rate
Loan Tenure
```

Outputs:

```text
Monthly EMI
Total Interest
Total Repayment
```

---

## 21.2 Stable Savings Basis

Use:

```text
Average Monthly Savings =
Average of valid monthly savings
over the trailing 3 months
```

This prevents one unusual month from completely changing the affordability result.

---

## 21.3 EMI Rules

```text
IF
    EMI > Average Monthly Savings
THEN
    HIGH_PRESSURE
```

Otherwise:

```text
IF
    EMI > 75% of Average Monthly Savings
THEN
    SIGNIFICANT_COMMITMENT
```

Otherwise:

```text
POTENTIALLY_MANAGEABLE
```

Example:

```text
Average Monthly Savings = ₹15,000
EMI = ₹6,000

EMI / Savings = 40%
```

Result:

```text
POTENTIALLY_MANAGEABLE
```

The UI should clearly state that this is based on recorded financial data and is not professional financial advice.

---

# 22. Insight Output Schema

Every generated insight should follow a consistent structure.

```json
{
  "rule_id": "RB-05",
  "group": "EXPENSE_PRESSURE",
  "severity": "WARNING",
  "priority": 1,
  "title": "Expenses growing faster than income",
  "message": "Your expenses rose 13.3% while your income rose 4.0%.",
  "evidence": {
    "income_growth_pct": 4.0,
    "expense_growth_pct": 13.33,
    "period": "2026-08",
    "compared_with": "2026-07"
  }
}
```

## Required fields

### `rule_id`

Identifies the exact rule.

Example:

```text
RB-05
```

### `group`

Identifies the logical insight group.

Example:

```text
EXPENSE_PRESSURE
```

### `severity`

Possible values:

```text
INFO
WARNING
POSITIVE
```

### `priority`

Lower numbers indicate higher priority.

```text
1 = Highest
2 = Medium
3 = Lower
```

### `title`

Short human-readable insight title.

### `message`

The complete user-facing explanation.

### `evidence`

Contains the numerical values used to trigger the rule.

The evidence block is important for auditability, testing, and viva explanation.

---

# 23. Evidence Requirements

An insight should never be generated without sufficient evidence.

For example, RB-05 should contain:

```text
income_growth_pct
expense_growth_pct
current_period
previous_period
```

RB-02 should contain:

```text
category
current_category_share_pct
historical_average_share_pct
deviation_ratio
period
```

RB-03 should contain:

```text
income
expenses
savings
savings_rate
threshold
period
```

This allows the system to answer:

> "Why did FinZave generate this insight?"

with the exact values that caused the rule to fire.

---

# 24. Insight Deduplication Groups

The engine uses explicit groups.

## EXPENSE_PRESSURE

```text
RB-01
RB-03
RB-04
RB-05
```

These rules may describe related financial pressure.

## SPENDING_CONCENTRATION

```text
RB-02
RB-06
RB-07
```

These rules concern category/discretionary spending patterns.

## INCOME_PROFILE

```text
RB-09
```

## POSITIVE

```text
RB-08
```

---

# 25. Deduplication Strategy

When multiple rules fire inside one group:

```text
1. Sort by priority.
2. Select the lowest priority number as the primary insight.
3. Keep other non-redundant findings as supporting evidence/bullets.
4. Do not display duplicate messages describing the same underlying condition.
```

Example:

```text
EXPENSE_PRESSURE

RB-01 → priority 1
RB-04 → priority 1
RB-05 → priority 1
```

The frontend may show:

```text
Primary:
Expenses are increasing consistently.

Supporting findings:
• Savings have declined over recent periods.
• Expenses grew faster than income.
```

The exact presentation can be implemented at the frontend layer while the backend provides the structured data.

---

# 26. Worked Example — Complete and Traceable

This example uses complete three-month data.

## 26.1 Monthly Income

| Month | Fixed Income | Variable Income | Total Income |
|---|---:|---:|---:|
| June | ₹45,000 | ₹5,000 | ₹50,000 |
| July | ₹45,000 | ₹7,000 | ₹52,000 |
| August | ₹45,000 | ₹10,000 | ₹55,000 |

## 26.2 Monthly Expenses

| Month | Total Expenses | Savings | Savings Rate |
|---|---:|---:|---:|
| June | ₹30,000 | ₹20,000 | 40.00% |
| July | ₹35,000 | ₹17,000 | 32.69% |
| August | ₹42,000 | ₹13,000 | 23.64% |

Calculations:

```text
June:
₹50,000 - ₹30,000 = ₹20,000

July:
₹52,000 - ₹35,000 = ₹17,000

August:
₹55,000 - ₹42,000 = ₹13,000
```

Savings trend:

```text
₹20,000 → ₹17,000 → ₹13,000
```

Therefore savings are declining.

---

## 26.3 Category Data

| Category | June | July | August |
|---|---:|---:|---:|
| Rent | ₹15,000 | ₹15,000 | ₹15,000 |
| Food | ₹6,000 | ₹8,000 | ₹16,000 |
| Transport | ₹3,000 | ₹4,000 | ₹5,000 |
| Entertainment | ₹2,000 | ₹3,000 | ₹4,000 |
| Others | ₹4,000 | ₹5,000 | ₹2,000 |
| **Total** | **₹30,000** | **₹35,000** | **₹42,000** |

### August category shares

```text
Rent:
15,000 / 42,000 × 100 ≈ 35.71%

Food:
16,000 / 42,000 × 100 ≈ 38.10%

Transport:
5,000 / 42,000 × 100 ≈ 11.90%

Entertainment:
4,000 / 42,000 × 100 ≈ 9.52%

Others:
2,000 / 42,000 × 100 ≈ 4.76%
```

### Historical Food share

June:

```text
6,000 / 30,000 × 100 = 20%
```

July:

```text
8,000 / 35,000 × 100 ≈ 22.86%
```

Historical average:

```text
(20 + 22.86) / 2
≈ 21.43%
```

August:

```text
38.10%
```

Deviation:

```text
38.10 / 21.43
≈ 1.78×
```

Therefore:

```text
38.10% >= 30%
AND
1.78× >= 1.5×
```

RB-02 fires.

---

# 27. Worked Example — Rule Trace Table

| Rule | Computed Evidence | Threshold / Condition | Fires? |
|---|---|---|---|
| RB-01 | Expenses: ₹30k → ₹35k → ₹42k | 3-period increasing trend | **Yes** |
| RB-02 | Food: 38.10% vs 21.43% historical average | ≥30% and ≥1.5× average | **Yes** |
| RB-03 | August savings rate = 23.64% | `<20%` | **No** |
| RB-04 | Savings: ₹20k → ₹17k → ₹13k | 3-period declining trend | **Yes** |
| RB-05 | Income growth ≈ 5.77%; expense growth = 20.00% | Expense growth > 0 and > income growth | **Yes** |
| RB-06 | Discretionary = ₹4k + ₹4k = ₹8k; 8k/42k ≈ 19.05% | ≥30% | **No** |
| RB-07 | Food deviation ≈ 1.78× historical average | ≥1.5× | **Yes**, but deduplicated with RB-02 |
| RB-08 | Savings rate = 23.64%; savings declining | Requires positive/stable-or-increasing savings | **No** |
| RB-09 | Fixed income = ₹45k / ₹55k ≈ 81.82% | Informational | **Yes** |

This example demonstrates that every insight can be traced back to complete source data and a documented rule.

---

# 28. Example Generated Insights

After deduplication, the system might return:

### Insight 1 — Expense Pressure

```json
{
  "rule_id": "RB-05",
  "group": "EXPENSE_PRESSURE",
  "severity": "WARNING",
  "priority": 1,
  "title": "Expenses growing faster than income",
  "message": "Your expenses rose by 20.0% while your income rose by 5.8%.",
  "evidence": {
    "income_growth_pct": 5.77,
    "expense_growth_pct": 20.0,
    "period": "2026-08",
    "compared_with": "2026-07"
  }
}
```

### Insight 2 — Savings Trend

```json
{
  "rule_id": "RB-04",
  "group": "EXPENSE_PRESSURE",
  "severity": "WARNING",
  "priority": 1,
  "title": "Savings are declining",
  "message": "Your savings decreased from ₹20,000 in June to ₹13,000 in August.",
  "evidence": {
    "period_values": {
      "2026-06": 20000,
      "2026-07": 17000,
      "2026-08": 13000
    }
  }
}
```

### Insight 3 — Food Spending Deviation

```json
{
  "rule_id": "RB-02",
  "group": "SPENDING_CONCENTRATION",
  "severity": "INFO",
  "priority": 2,
  "title": "Food spending is unusually high",
  "message": "Food represents 38.1% of your spending this month, compared with your historical average of 21.4%.",
  "evidence": {
    "category": "Food",
    "current_share_pct": 38.10,
    "historical_average_share_pct": 21.43,
    "deviation_ratio": 1.78,
    "period": "2026-08"
  }
}
```

RB-07 is not shown separately because it describes the same underlying category deviation.

---

# 29. Handling Insufficient Data

The algorithm must distinguish between:

```text
NO DATA
INSUFFICIENT DATA
VALID RESULT
```

Examples:

### No income

```text
Savings Rate = UNAVAILABLE
```

### One period only

```text
Trend = INSUFFICIENT_DATA
```

### Previous value is zero

```text
Percentage Change = INSUFFICIENT_DATA
```

### Fewer than three periods for a 3-period trend

```text
Consecutive Trend = INSUFFICIENT_DATA
```

### No historical category data

```text
RB-02 = INSUFFICIENT_DATA
```

The system must not generate a trend or comparison from data that cannot support it.

---

# 30. Full Algorithm Pseudocode

```text
FUNCTION analyze_finances(user_id, current_period):

    income_data = load_income(user_id)
    expense_data = load_expenses(user_id)

    validate_records(income_data)
    validate_records(expense_data)

    monthly_metrics = calculate_monthly_metrics(
        income_data,
        expense_data
    )

    FOR each month:

        total_income =
            fixed_income + variable_income

        total_expenses =
            sum(valid_expenses)

        savings =
            total_income - total_expenses

        IF total_income > 0:
            savings_rate =
                (savings / total_income) * 100
        ELSE:
            savings_rate = UNAVAILABLE

    period_comparisons =
        calculate_period_changes(monthly_metrics)

    FOR each comparison:

        IF previous_value == 0:
            comparison = INSUFFICIENT_DATA
        ELSE:
            change_pct =
                ((current - previous) / previous) * 100

            classify as:
                INCREASING
                STABLE
                DECREASING

    category_analysis =
        calculate_category_shares(expense_data)

    historical_category_analysis =
        calculate_historical_category_averages(expense_data)

    insights = []

    evaluate RB-01
    evaluate RB-02
    evaluate RB-03
    evaluate RB-04
    evaluate RB-05
    evaluate RB-06
    evaluate RB-07
    evaluate RB-08
    evaluate RB-09

    assign severity
    assign priority

    deduplicate by insight group

    create analysis result

    store analysis result

    invalidate/update cache

    RETURN analysis result
```

---

# 31. SIP/EMI Pseudocode

```text
FUNCTION calculate_financial_commitment(user_id, commitment):

    monthly_savings =
        calculate_valid_monthly_savings(user_id)

    trailing_average =
        average(last 3 valid monthly savings)

    IF fewer than required valid months:
        RETURN INSUFFICIENT_DATA

    ratio =
        commitment / trailing_average

    IF commitment > trailing_average:
        status = MAY_NOT_BE_PRACTICAL

    ELSE IF ratio > 0.75:
        status = HIGH_COMMITMENT

    ELSE:
        status = POTENTIALLY_MANAGEABLE

    RETURN status
```

The SIP and EMI calculators remain mathematically separate from this affordability-analysis layer.

---

# 32. Rule Engine Output

The complete analysis result can contain:

```text
Analysis
├── Period
├── Total Income
├── Total Expenses
├── Savings
├── Savings Rate
├── Income Trend
├── Expense Trend
├── Savings Trend
├── Category Distribution
├── Income Profile
└── Insights
    ├── Primary Insights
    └── Supporting Evidence
```

---

# 33. Persistence

The final derived analysis should be stored in the `analyses` table.

The transaction tables remain the source of truth.

```text
Income + Expenses
       ↓
Analysis Engine
       ↓
Derived Analysis
       ↓
analyses table
       ↓
Cache
```

The analysis table should contain enough information to reconstruct the displayed analytical result without recalculating the entire transaction history on every dashboard request.

---

# 34. Cache Interaction

When financial data changes:

```text
Add Income
Edit Income
Delete Income
Add Expense
Edit Expense
Delete Expense
```

the system should:

```text
1. Save transaction
2. Recalculate affected analysis
3. Store updated analysis
4. Invalidate/update user analysis cache
```

Dashboard requests should normally read the cached/precomputed result.

---

# 35. Testing Strategy

Every rule should have at least:

### Positive test

A dataset where the rule must fire.

### Negative test

A dataset where the rule must not fire.

### Boundary test

A dataset exactly at the threshold.

### Insufficient-data test

A dataset that cannot support the rule.

### Zero-value test

Where applicable, a previous value of zero.

Example for RB-05:

```text
Test 1:
Income +4%
Expenses +13.33%
Expected → FIRE

Test 2:
Income -20%
Expenses -5%
Expected → DO NOT FIRE

Test 3:
Income +5%
Expenses +5%
Expected → DO NOT FIRE

Test 4:
Previous income = 0
Expected → INSUFFICIENT_DATA
```

---

# 36. Explainability and Viva Justification

The strongest technical justification for FinZave's rule-based approach is that every result can be audited.

For example:

```text
Insight
   ↓
RB-05
   ↓
Expense Growth = 13.33%
Income Growth = 4.00%
   ↓
13.33 > 4.00
   ↓
Rule condition satisfied
   ↓
Insight generated
```

There is no hidden model decision.

This allows the developer to explain:

> "Every FinZave insight is generated from a documented deterministic rule and contains the numerical evidence used by that rule."

This is one of the major advantages of the architecture for an academic mini project.

---

# 37. Scope Restrictions

The current rule engine must not introduce:

- Machine Learning
- Deep Learning
- LLM-based recommendations
- AI financial advisors
- Stock prediction
- Mutual fund recommendations
- Live market analysis
- Market prediction
- Investment scoring systems

These remain outside the current scope.

---

# 38. Future Enhancements

Possible future enhancements include:

- Machine-learning-based forecasting
- Advanced spending prediction
- Receipt-based automatic categorization
- Bank transaction import
- AI conversational assistance
- Advanced financial forecasting
- Distinct fixed-income pressure rule

These should remain future enhancements unless the project scope is explicitly changed.

---

# 39. Final Rule Set

The finalized core rule set is:

| Rule | Purpose |
|---|---|
| **RB-01** | Detect persistent increasing expenses |
| **RB-02** | Detect unusually high category spending compared with the user's own history |
| **RB-03** | Detect savings rate below the project threshold |
| **RB-04** | Detect persistent declining savings |
| **RB-05** | Detect expenses increasing faster than income |
| **RB-06** | Detect significant discretionary spending |
| **RB-07** | Detect historical category deviation without requiring a budget table |
| **RB-08** | Identify positive/stable savings behaviour |
| **RB-09** | Analyse fixed vs variable income composition |

There is **no RB-10 expense-ratio rule**, because it is mathematically identical to RB-03.

---

# 40. Final Definition

The FinZave Rule-Based Financial Analysis Algorithm is a deterministic and explainable system that processes user financial records, calculates financial metrics, compares current behaviour with previous periods and personal historical patterns, evaluates predefined rules, and generates auditable financial insights.

Its defining pipeline is:

```text
TRACK
  ↓
COLLECT
  ↓
VALIDATE
  ↓
CALCULATE
  ↓
COMPARE
  ↓
ANALYSE PERSONAL PATTERNS
  ↓
EVALUATE RULES
  ↓
GENERATE EVIDENCE-BACKED INSIGHTS
  ↓
DEDUPLICATE
  ↓
PRIORITIZE
  ↓
STORE
  ↓
CACHE
  ↓
PRESENT
```

The goal is not to predict financial markets or replace professional financial advice.

The goal is to make FinZave capable of answering:

> **"What does my own financial data tell me about my current financial behaviour, and what patterns should I pay attention to?"**
