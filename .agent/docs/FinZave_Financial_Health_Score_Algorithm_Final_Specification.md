# FinZave Financial Health Score Algorithm Specification

## Version

1.0

## Purpose

This document defines the complete missing specification required to
implement the FinZave Financial Health Score Engine.

The Rule Engine is responsible for detecting financial behaviour.

The Health Score Engine is responsible for converting detected behaviour
into a measurable score.

The system flow:

    Financial Transactions

            ↓

    Financial Metrics

            ↓

    Rule Engine

            ↓

    Rule Insights

            ↓

    Health Score Engine

            ↓

    0-100 Financial Health Score

------------------------------------------------------------------------

# 1. Responsibility Separation

## Rule Engine

The Rule Engine answers:

"What happened?"

It performs:

-   threshold evaluation
-   financial behaviour detection
-   evidence generation
-   severity assignment

Examples:

    RB-03:
    Low Savings Rate

    RB-05:
    Expenses Growing Faster Than Income

    RB-08:
    Positive Savings Pattern

------------------------------------------------------------------------

## Health Score Engine

The Health Score Engine answers:

"How does the detected behaviour affect overall financial health?"

It performs:

-   score calculation
-   rule impact aggregation
-   normalization
-   explanation generation

It must NOT:

-   recalculate Rule Engine conditions
-   create new financial rules
-   analyse raw transactions directly

------------------------------------------------------------------------

# 2. Score Range

Final score:

    0 - 100

Score boundaries:

    Minimum = 0

    Maximum = 100

------------------------------------------------------------------------

# 3. Starting Score

The engine starts from a neutral financial position.

    BASE_SCORE = 50

The score changes based on detected financial behaviours.

------------------------------------------------------------------------

# 4. Rule Impact Configuration

The following table defines the Health Score impact layer.

This table is independent from Rule Engine thresholds.

  Rule ID   Behaviour                             Severity   Impact
  --------- ------------------------------------- ---------- --------
  RB-01     Increasing Expenses                   WARNING    -10
  RB-02     Category Spending Deviation           WARNING    -8
  RB-03     Low Savings Rate                      WARNING    -15
  RB-04     Declining Savings                     WARNING    -10
  RB-05     Expenses Growing Faster Than Income   WARNING    -15
  RB-06     High Discretionary Spending           WARNING    -10
  RB-07     Historical Category Overspending      WARNING    -8
  RB-08     Positive Savings Pattern              POSITIVE   +10
  RB-09     Income Profile                        INFO       0

------------------------------------------------------------------------

# 5. Calculation Formula

The Health Score calculation:

    score = BASE_SCORE

For every triggered rule:

    IF severity == WARNING:

        score = score + negative impact


    IF severity == POSITIVE:

        score = score + positive impact


    IF severity == INFO:

        score = score + 0

Final:

    Health Score = clamp(score,0,100)

------------------------------------------------------------------------

# 6. Example Calculation

Input:

    RB-03 WARNING
    RB-05 WARNING
    RB-08 POSITIVE

Calculation:

    Starting Score:

    50


    RB-03:

    50 - 15

    =35


    RB-05:

    35 - 15

    =20


    RB-08:

    20 + 10

    =30

Final:

    Health Score = 30

------------------------------------------------------------------------

# 7. Behaviour Categories

## Savings Behaviour

Rules:

    RB-03
    RB-04
    RB-08

Impact:

Measures:

-   savings discipline
-   savings consistency
-   savings improvement

------------------------------------------------------------------------

## Expense Management

Rules:

    RB-01
    RB-05

Impact:

Measures:

-   expense control
-   income versus expense pressure

------------------------------------------------------------------------

## Spending Behaviour

Rules:

    RB-02
    RB-06
    RB-07

Impact:

Measures:

-   category spending behaviour
-   discretionary spending
-   overspending patterns

------------------------------------------------------------------------

## Income Profile

Rule:

    RB-09

Impact:

Context only.

Default:

    0 points

------------------------------------------------------------------------

# 8. Duplicate Behaviour Protection

The same financial problem should not reduce the score multiple times.

Example:

    RB-02

    and

    RB-07

Both may represent category overspending.

Processing:

1.  Group related insights.
2.  Detect duplicate behaviour.
3.  Apply maximum relevant impact.
4.  Keep all evidence.

Example:

Without protection:

    -8 + -8 = -16

With protection:

    Maximum category penalty = -8

------------------------------------------------------------------------

# 9. Positive and Negative Rules Together

Positive and negative behaviours can exist simultaneously.

Example:

    RB-08 = +10

    RB-05 = -15

Calculation:

    50 + 10 - 15

    =45

The score represents the combined financial state.

------------------------------------------------------------------------

# 10. Score Categories

  Score Range   Category
  ------------- -----------------
  90-100        Excellent
  75-89         Good
  50-74         Moderate
  25-49         Needs Attention
  0-24          Critical

------------------------------------------------------------------------

# 11. Insufficient Data Handling

If the user has insufficient financial history:

Return:

``` json
{
 "status":"INSUFFICIENT_DATA",
 "score":null
}
```

Do not create an artificial score.

------------------------------------------------------------------------

# 12. Zero Income Handling

The Health Score Engine must rely on Rule Engine output.

It must not independently calculate financial ratios.

Division handling belongs to:

-   finance.py
-   financial_metrics.py
-   rule_engine.py

------------------------------------------------------------------------

# 13. Output Contract

Example:

``` json
{
 "score":65,

 "category":"Moderate",

 "adjustments":[

 {
  "rule_id":"RB-03",
  "impact":-15,
  "reason":"Low savings rate detected",
  "evidence":{}
 }

 ]
}
```

------------------------------------------------------------------------

# 14. Implementation Contract

File:

    analysis/scoring.py

Required functions:

    calculate_health_score()

    apply_rule_impacts()

    normalize_score()

    generate_explanation()

------------------------------------------------------------------------

# 15. Testing Requirements

## Rule Impact Testing

Verify every rule applies the correct impact.

## Multi Rule Testing

Verify multiple rules combine correctly.

## Duplicate Testing

Verify duplicate behaviours do not stack incorrectly.

## Boundary Testing

Verify:

    0 <= score <= 100

## Empty Data Testing

Verify:

    INSUFFICIENT_DATA

------------------------------------------------------------------------

# 16. Final Definition

FinZave intelligence layers:

    Metrics Layer

    Calculates financial values.


    Rule Engine

    Detects financial behaviour.


    Health Score Engine

    Converts behaviour into a score.


    Dashboard

    Explains the result.

The Health Score Engine is the scoring layer, not the detection layer.
