"""
Module: analysis/scoring.py

Purpose:
Performs algorithmic health scoring and complex financial analysis.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import logging
from typing import List, Dict, Any, Optional
from utils.rule_engine import FinancialPeriod

logger = logging.getLogger(__name__)

def normalize_score(score: int) -> int:
    """Clamps the score between 0 and 100."""
    return max(0, min(100, score))

def get_score_category(score: int) -> str:
    """
    Returns the descriptive category based on the health score:
    0-49: Needs Improvement
    50-74: Moderate
    75-89: Good
    90-100: Excellent
    """
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 50:
        return "Moderate"
    else:
        return "Needs Improvement"

def calculate_data_confidence(periods: List[FinancialPeriod]) -> float:
    """
    Calculates the confidence factor (between 0.50 and 1.00) based on:
    1. Financial history length (<3 months: low, 3-6: medium, 6-9: high, 9-11: robust, 12+: complete)
    2. Data coverage and tracking consistency (income and expenses present)
    3. Missing financial dimensions (investments, debt/liabilities, emergency buffer)
    """
    if not periods:
        return 0.50
        
    active_periods = [p for p in periods if p.status != "no_data"]
    n_months = len(active_periods)
    if n_months == 0:
        return 0.50

    # 1. Number of months available
    if n_months < 3:
        history_factor = 0.65
    elif n_months < 6:
        history_factor = 0.78
    elif n_months < 9:
        history_factor = 0.85
    elif n_months < 12:
        history_factor = 0.90  # 9-11 months robust base
    else:
        history_factor = 1.00  # 12+ months complete history

    # 2. Data coverage & consistency
    months_with_income = sum(1 for p in active_periods if p.total_income > 0)
    income_coverage = months_with_income / n_months

    months_with_expenses = sum(1 for p in active_periods if p.total_expenses > 0)
    expense_coverage = months_with_expenses / n_months

    coverage_factor = (income_coverage * 0.5) + (expense_coverage * 0.5)

    # 3. Missing financial dimensions
    all_categories = set()
    for p in active_periods:
        all_categories.update(p.categories.keys())
        
    has_investments = any(c in all_categories for c in {'Investment', 'Investments', 'SIP', 'Mutual Funds', 'Stocks'})
    
    # Missing wealth/investment dimension adjustment
    dimension_adjustment = 0.0 if has_investments else -0.05

    confidence = (history_factor * coverage_factor) + dimension_adjustment
    return max(0.50, min(1.0, round(confidence, 2)))

def calculate_health_score(periods: List[FinancialPeriod], metrics_has_data: bool, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates the final Health Score using a weighted financial health model (Total = 100 points):
    - Pillar 1: Savings Rate (40 points)
    - Pillar 2: Expense Ratio (25 points)
    - Pillar 3: Financial Stability and Trend (20 points)
    - Pillar 4: Spending Control (15 points)
    Adjusted by data confidence (0.50 to 1.00) based on history length and completeness.
    """
    if not metrics_has_data or not periods:
        return {
            "status": "INSUFFICIENT_DATA",
            "score": None,
            "raw_score": None,
            "confidence": None,
            "category": None,
            "adjustments": []
        }
        
    current = periods[-1]
    prev = periods[-2] if len(periods) >= 2 else None
    
    # ----------------------------------------------------
    # PILLAR 1: Savings Rate (40 points)
    # <10%: 5 pts, 10%-20%: 15 pts, 20%-40%: 28 pts, >40%: 40 pts
    # ----------------------------------------------------
    savings_rate = current.savings_rate
    if current.total_income > 0 and current.savings > 0 and savings_rate is not None:
        if savings_rate < 0.10:
            p1_score = 5
        elif savings_rate < 0.20:
            p1_score = 15
        elif savings_rate <= 0.40:
            p1_score = 28
        else:
            p1_score = 40
    else:
        p1_score = 0
        
    # ----------------------------------------------------
    # PILLAR 2: Expense Ratio (25 points)
    # Expenses <50% of income: 25 pts
    # 50%-70%: 18 pts, 70%-90%: 10 pts, 90%-100%: 5 pts, >100% or income<=0: 0 pts
    # ----------------------------------------------------
    p2_score = 0
    if current.total_income > 0:
        expense_ratio = current.total_expenses / current.total_income
        if expense_ratio < 0.50:
            p2_score = 25
        elif expense_ratio <= 0.70:
            p2_score = 18
        elif expense_ratio <= 0.90:
            p2_score = 10
        elif expense_ratio <= 1.00:
            p2_score = 5
        else:
            p2_score = 0
    else:
        p2_score = 0

    # ----------------------------------------------------
    # PILLAR 3: Financial Stability and Trend (20 points)
    # - Savings Trend (10 pts):
    #   Savings improved or stable MoM or RB-08 present: 10 pts
    #   Minor drop (<=10% drop): 6 pts
    #   Severe drop or RB-04 present: 2 pts
    # - Income Stability (10 pts):
    #   Income > 0 and consistent/stable: 10 pts
    #   Income drop > 20%: 5 pts
    #   No income: 0 pts
    # ----------------------------------------------------
    p3_savings_trend = 0
    has_rb08 = any(i.get("rule_id") == "RB-08" for i in insights)
    has_rb04 = any(i.get("rule_id") == "RB-04" for i in insights)
    
    if prev and prev.total_income > 0:
        if current.savings >= prev.savings or has_rb08:
            p3_savings_trend = 10
        elif has_rb04:
            p3_savings_trend = 2
        else:
            pct_drop = (prev.savings - current.savings) / abs(prev.savings) if prev.savings != 0 else 1.0
            p3_savings_trend = 6 if pct_drop <= 0.10 else 2
    else:
        p3_savings_trend = 8 if (current.savings > 0 and current.total_income > 0) else 0

    p3_income_stability = 0
    if current.total_income > 0:
        if prev and prev.total_income > 0:
            if current.total_income >= prev.total_income * 0.80:
                p3_income_stability = 10
            else:
                p3_income_stability = 5
        else:
            p3_income_stability = 10
    else:
        p3_income_stability = 0

    p3_score = min(20, p3_savings_trend + p3_income_stability)

    # ----------------------------------------------------
    # PILLAR 4: Spending Control (15 points)
    # - Discretionary spending control (8 pts):
    #   RB-06 NOT triggered: 8 pts, else 2 pts
    # - Expense Discipline & Spikes control (7 pts):
    #   Neither RB-01 nor RB-05 triggered: 7 pts
    #   One triggered: 3 pts, both triggered: 0 pts
    # ----------------------------------------------------
    has_rb06 = any(i.get("rule_id") == "RB-06" for i in insights)
    p4_discretionary = 2 if has_rb06 else 8

    has_rb01 = any(i.get("rule_id") == "RB-01" for i in insights)
    has_rb05 = any(i.get("rule_id") == "RB-05" for i in insights)
    if not has_rb01 and not has_rb05:
        p4_discipline = 7
    elif has_rb01 and has_rb05:
        p4_discipline = 0
    else:
        p4_discipline = 3

    p4_score = min(15, p4_discretionary + p4_discipline)

    raw_score = p1_score + p2_score + p3_score + p4_score
    confidence = calculate_data_confidence(periods)
    final_score = normalize_score(int(round(raw_score * confidence)))
    category = get_score_category(final_score)

    adjustments = [
        {"pillar": "Savings Rate", "score": p1_score, "max": 40, "reason": f"Savings rate is {(current.savings_rate or 0)*100:.1f}%"},
        {"pillar": "Expense Ratio", "score": p2_score, "max": 25, "reason": f"Expenses are {(current.total_expenses/current.total_income*100) if current.total_income > 0 else 100:.1f}% of income"},
        {"pillar": "Financial Stability", "score": p3_score, "max": 20, "reason": "Evaluated based on savings trajectory and income continuity"},
        {"pillar": "Spending Control", "score": p4_score, "max": 15, "reason": "Evaluated based on discretionary and recurring spending discipline"}
    ]

    return {
        "status": "SUCCESS",
        "score": final_score,
        "raw_score": raw_score,
        "confidence": int(round(confidence * 100)),
        "category": category,
        "adjustments": adjustments,
        "pillars": {
            "savings_rate": {"score": p1_score, "max": 40},
            "expense_ratio": {"score": p2_score, "max": 25},
            "stability_trend": {"score": p3_score, "max": 20},
            "spending_control": {"score": p4_score, "max": 15}
        }
    }
