# FinZave Analysis Module Final Implementation Blueprint

## Purpose

This document is the final implementation guide for the FinZave Analysis
Module redesign.

This replaces all previous implementation approaches.

The objective is to build a complete financial intelligence analysis
system while maintaining ONE financial calculation pipeline.

The new Analysis module must extend the existing FinZave intelligence
system, not create a parallel calculation engine.

------------------------------------------------------------------------

# Core Architecture Principle

## Single Source of Financial Truth

The architecture must follow:

Transactions \| v Financial Calculation Engine (utils/finance.py) \|
+----------------+ \| \| v v Rule Engine Analysis Engine \| \| v v
Health Score Monthly Comparison \| Yearly Comparison v Insights
Recommendations

All modules must consume the same financial calculations.

------------------------------------------------------------------------

# Critical Rules

## DO NOT create a separate financial calculation engine.

The following must NOT be duplicated:

-   Income calculation
-   Expense calculation
-   Savings calculation
-   Category aggregation
-   Financial period generation

The Analysis module must reuse and extend the existing finance engine.

------------------------------------------------------------------------

# Existing Core Modules

## Transaction Layer

Responsible for:

-   Expense storage
-   Income storage
-   Categories
-   Dates
-   Transaction validation

Files:

    models/expense.py
    models/income.py
    routes/transactions.py

Do not redesign transaction storage.

------------------------------------------------------------------------

# Financial Engine

Location:

    utils/finance.py

Responsibility:

This is the financial truth layer.

It calculates:

-   Income totals
-   Expense totals
-   Savings
-   Savings percentage
-   Financial periods
-   Historical financial data

The new Analysis module must consume this layer.

------------------------------------------------------------------------

# Controlled Finance Engine Extension

Modification to utils/finance.py is allowed only when required.

Examples:

Allowed:

Adding:

    get_financial_summary()

or:

    aggregate_financial_period()

if the existing engine cannot provide required data.

Not allowed:

Creating duplicate calculations inside:

    analysis/services/

------------------------------------------------------------------------

# Rule Engine Integration

Location:

    utils/rule_engine.py

Responsibility:

Detect financial behaviour.

Examples:

-   Increasing expenses
-   Low savings rate
-   Spending imbalance

The Analysis module should consume Rule Engine outputs.

It should not recreate rules.

------------------------------------------------------------------------

# Health Score Integration

The Analysis Overview must display:

-   Current health score
-   Score explanation
-   Positive factors
-   Negative factors
-   Improvement suggestions

Health Score calculation remains unchanged.

------------------------------------------------------------------------

# New Analysis Structure

The redesigned Analysis module contains three sections.

    Analysis

    |
    |-- Overview
    |
    |-- Monthly Comparison
    |
    |-- Yearly Comparison

------------------------------------------------------------------------

# Backend Architecture

Recommended structure:

    analysis/

    services/

        overview_service.py

        monthly_service.py

        yearly_service.py

        insight_service.py


    calculators/

        comparison_calculator.py

        growth_calculator.py

        category_calculator.py


    utils/

        analysis_helpers.py


    schemas/

        analysis_schema.py

------------------------------------------------------------------------

# Service Responsibilities

## overview_service.py

Purpose:

Build current financial condition.

Consumes:

-   Finance Engine
-   Rule Engine
-   Health Score
-   Recommendations

Returns:

-   Financial summary
-   Health information
-   Insights
-   Recommendations

------------------------------------------------------------------------

## monthly_service.py

Purpose:

Compare current month against previous month.

Must NOT calculate finances independently.

Uses Finance Engine output.

Calculates:

-   Income change
-   Expense change
-   Savings change
-   Savings rate change
-   Category movement

------------------------------------------------------------------------

## yearly_service.py

Purpose:

Compare current year against previous year.

Calculates:

-   Annual income growth
-   Annual expense growth
-   Annual savings growth
-   Average monthly savings
-   Category trends

------------------------------------------------------------------------

# API Specification

## Overview API

Endpoint:

    GET /app/api/analysis/overview

Authentication:

JWT required.

Response:

``` json
{
 "health_score": {},
 "summary": {
   "income":0,
   "expense":0,
   "savings":0,
   "saving_rate":0
 },
 "insights":[],
 "recommendations":[]
}
```

------------------------------------------------------------------------

# Monthly Comparison API

Endpoint:

    GET /app/api/analysis/monthly

Parameters:

    year
    month

Example:

    /app/api/analysis/monthly?year=2026&month=9

Response:

``` json
{
 "period":{
   "current":"",
   "previous":""
 },
 "comparison":{
   "income":{},
   "expense":{},
   "savings":{},
   "saving_rate":{}
 },
 "categories":[],
 "insights":[]
}
```

------------------------------------------------------------------------

# Yearly Comparison API

Endpoint:

    GET /app/api/analysis/yearly

Parameter:

    year

Response:

``` json
{
 "years":{
   "current":2026,
   "previous":2025
 },
 "comparison":{
   "income":{},
   "expense":{},
   "savings":{}
 },
 "monthly_average":{},
 "categories":[],
 "insights":[]
}
```

------------------------------------------------------------------------

# Calculation Rules

## Savings

    income - expense

## Savings Rate

    (savings / income) * 100

## Percentage Change

    ((current - previous) / previous) * 100

Handle:

-   Zero values
-   No previous month
-   New users
-   Empty history

------------------------------------------------------------------------

# Database Strategy

No new tables should be created.

Use existing:

-   users
-   expenses
-   incomes
-   goals

Queries must always include:

    user_id

Never expose another user's financial data.

------------------------------------------------------------------------

# Frontend Requirements

## Overview Page

Sections:

1.  Financial Health

2.  Financial Snapshot

3.  Spending Behaviour

4.  Insights

5.  Recommendations

------------------------------------------------------------------------

## Monthly Comparison Page

Sections:

1.  Current vs Previous Month cards

2.  Income comparison

3.  Expense comparison

4.  Savings comparison

5.  Category changes

6.  Explanation insights

------------------------------------------------------------------------

## Yearly Comparison Page

Sections:

1.  Annual growth summary

2.  Income trend

3.  Expense trend

4.  Savings progress

5.  Category behaviour

------------------------------------------------------------------------

# Security Requirements

All APIs require:

-   Authentication
-   User isolation
-   Backend controlled calculations

Never calculate financial values in JavaScript.

------------------------------------------------------------------------

# Performance Requirements

Avoid:

-   Loading unnecessary transactions
-   Duplicate calculations
-   N+1 queries

Use:

-   Existing aggregation functions
-   SQL grouping where required
-   Efficient date filtering

------------------------------------------------------------------------

# Testing Requirements

Create:

    tests/

    test_analysis_overview.py

    test_analysis_monthly.py

    test_analysis_yearly.py

    test_analysis_security.py

Test:

## Overview

-   Health score loading
-   Rule integration
-   Empty user state

## Monthly

-   Current month comparison
-   Previous month comparison
-   Percentage calculations

## Yearly

-   Annual aggregation
-   Growth calculations

## Security

-   User isolation
-   Unauthorized requests

------------------------------------------------------------------------

# Implementation Order

## Phase 1

Audit existing finance engine.

Confirm reusable functions.

------------------------------------------------------------------------

## Phase 2

Extend finance engine only if required.

No duplicate calculations.

------------------------------------------------------------------------

## Phase 3

Create Analysis services.

------------------------------------------------------------------------

## Phase 4

Create APIs.

------------------------------------------------------------------------

## Phase 5

Redesign frontend.

------------------------------------------------------------------------

## Phase 6

Testing and optimization.

------------------------------------------------------------------------

# Final Agent Instructions

Before implementation:

1.  Inspect existing code.
2.  Verify current calculation flow.
3.  Reuse existing financial engine.
4.  Extend instead of duplicate.
5.  Maintain backward compatibility.
6.  Generate implementation report after completion.

The final goal:

FinZave Analysis should behave like a personal financial advisor by
explaining:

-   Where the user stands financially.
-   What changed.
-   Why it changed.
-   How the user can improve.

The system must have one financial truth and multiple intelligent views.

------------------------------------------------------------------------

# Financial Period Completeness Update

## Concept
A `FinancialPeriod` now has a `status` property which can be `complete`, `incomplete`, or `no_data`.

## Rules for Incomplete Months
1. Current month + income exists + no expenses: Status is "incomplete".
2. Previous completed months or current month with both income and expenses: Status is "complete".
3. New user with no financial activity: Status is "no_data".

## Analysis Behaviour Changes
When a month is incomplete:
- The Analysis Overview explicitly states that financial tracking is incomplete.
- Category breakdowns do not calculate misleading 100% reduction diffs.
- Savings impact insights avoid generating false positive insights based on zero expenses.
- Trends comparisons against previous months are halted to prevent rewarding incomplete tracking.

## Chart Empty State Rules
Charts in `analysis`, `analysis_monthly`, `analysis_yearly`, and `dashboard` must NEVER display empty graphs with axes and meaningless zero values for incomplete data.
- If data is incomplete, the chart area is replaced with a FinZave-styled empty state.
- Empty states use Lucide icons (e.g., `pie-chart`, `bar-chart`, `line-chart`) with descriptive messages like "Add expense records to unlock spending insights."

## Architectural Decisions
- `is_current_month` flag is injected into `FinancialPeriod` by `utils/finance.py`.
- `is_incomplete` flag is passed directly into template rendering logic by `analysis/services.py` and `utils/financial_metrics.py`.
- The rule evaluation in `utils/rule_engine.py` skips the current period if it is `incomplete` to prevent false positive rule-based insights.
- The `calculate_health_score` function in `analysis/scoring.py` inherently accounts for incomplete months by receiving filtered insights and avoids false rewards.
