from typing import List, Dict, Any
from utils.rule_engine import FinancialPeriod, percentage_change

def calculate_period_metrics(periods: List[FinancialPeriod]) -> Dict[str, Any]:
    """
    Transforms a list of chronological FinancialPeriod objects into structured metrics.
    Acts as a clean data layer between the raw financial periods and the UI.
    """
    if not periods:
        return {
            "has_data": False
        }
        
    current = periods[-1]
    
    # Check if the user has any data across all periods generated
    has_any_data = any((p.total_income > 0 or p.total_expenses > 0) for p in periods)
    
    if not has_any_data:
        return {
            "has_data": False
        }
    
    metrics = {
        "has_data": True,
        "current_period": {
            "period_id": current.period_id,
            "total_income": current.total_income,
            "total_expense": current.total_expenses,
            "total_savings": current.savings,
            "savings_rate": current.savings_rate if current.savings_rate is not None else 0.0,
            "categories": current.categories
        },
        "trends": {
            "income_change": 0.0,
            "expense_change": 0.0,
            "savings_change": 0.0
        },
        "chart_data": {
            "labels": [],
            "income": [],
            "expenses": [],
            "cat_labels": [],
            "cat_data": []
        }
    }
    
    # Calculate period-over-period trends if we have at least 2 periods
    if len(periods) >= 2:
        prev = periods[-2]
        
        income_change = percentage_change(current.total_income, prev.total_income)
        expense_change = percentage_change(current.total_expenses, prev.total_expenses)
        savings_change = percentage_change(current.savings, prev.savings)
        
        metrics["trends"]["income_change"] = (income_change * 100) if income_change is not None else 0.0
        metrics["trends"]["expense_change"] = (expense_change * 100) if expense_change is not None else 0.0
        metrics["trends"]["savings_change"] = (savings_change * 100) if savings_change is not None else 0.0
        
    # Generate Chart Data (up to 6 months)
    for p in periods[-6:]:
        metrics["chart_data"]["labels"].append(p.period_id)
        metrics["chart_data"]["income"].append(p.total_income)
        metrics["chart_data"]["expenses"].append(p.total_expenses)
        
    # Generate Category Distribution Chart Data (current month)
    sorted_cats = sorted(current.categories.items(), key=lambda x: x[1], reverse=True)
    metrics["chart_data"]["cat_labels"] = [k for k, v in sorted_cats]
    metrics["chart_data"]["cat_data"] = [v for k, v in sorted_cats]
    
    return metrics
