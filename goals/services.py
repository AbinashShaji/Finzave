"""
Module: goals/services.py

Purpose:
Core application logic and configurations.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from datetime import date
from typing import Dict, Any, List
from utils.rule_engine import FinancialPeriod

def calculate_goal_progress(goal) -> Dict[str, Any]:
    target = float(goal.target_amount) if getattr(goal, 'target_amount', None) is not None else 0.0
    saved = float(goal.current_saved) if getattr(goal, 'current_saved', None) is not None else 0.0
    
    if target <= 0:
        completion_pct = 0.0
        remaining = 0.0
    else:
        completion_pct = (saved / target) * 100.0
        remaining = max(0.0, target - saved)
        
    completion_pct = min(100.0, completion_pct)
    
    is_completed = saved >= target and target > 0
    is_overdue = date.today() > goal.target_date and not is_completed
    
    return {
        "saved": saved,
        "target": target,
        "remaining": remaining,
        "completion_pct": completion_pct,
        "is_completed": is_completed,
        "is_overdue": is_overdue
    }

def calculate_goal_affordability(goal, financial_periods: Any, progress_data: Dict[str, Any]) -> Dict[str, Any]:
    today = date.today()
    
    # Normalize input into a list of periods
    if financial_periods is None:
        periods_list = []
    elif isinstance(financial_periods, (list, tuple)):
        periods_list = list(financial_periods)
    else:
        periods_list = [financial_periods]
        
    # Filter active financial periods (exclude no_data periods)
    active_periods = []
    for p in periods_list:
        if p is None:
            continue
        status = getattr(p, 'status', None)
        if status == 'no_data':
            continue
        if hasattr(p, 'total_income') and hasattr(p, 'total_expenses'):
            if (p.total_income or 0.0) == 0.0 and (p.total_expenses or 0.0) == 0.0:
                continue
        active_periods.append(p)
        
    active_months = len(active_periods)
    
    if active_months > 0:
        has_history = True
        total_savings = 0.0
        for p in active_periods:
            if hasattr(p, 'total_income') and hasattr(p, 'total_expenses') and p.total_income is not None and p.total_expenses is not None:
                m_savings = float(p.total_income) - float(p.total_expenses)
            elif hasattr(p, 'savings') and p.savings is not None:
                m_savings = float(p.savings)
            else:
                m_savings = 0.0
            total_savings += m_savings
            
        average_savings_capacity = total_savings / active_months
        month_word = "month" if active_months == 1 else "months"
        context_message = f"Based on {active_months} {month_word} of financial history"
    else:
        has_history = False
        average_savings_capacity = 0.0
        context_message = "Not enough financial data to estimate savings capacity."

    if progress_data.get("is_completed"):
        msg = "You have successfully reached your goal target." if has_history else "Not enough financial data to estimate savings capacity."
        return {
            "req_monthly": 0.0,
            "average_savings_capacity": average_savings_capacity,
            "current_savings_capacity": average_savings_capacity,
            "impact_pct": 0.0,
            "raw_impact_pct": 0.0,
            "months_left": 0,
            "has_history": has_history,
            "active_months": active_months,
            "context_message": context_message,
            "impact_message": "Goal target achieved." if has_history else "Not enough financial data to estimate savings capacity.",
            "message": msg
        }
        
    target_date = goal.target_date
    months = (target_date.year - today.year) * 12 + target_date.month - today.month
    months_left = max(1, months if target_date >= today else 0)
    
    if progress_data.get("is_overdue"):
        months_left = 1 
        
    req_monthly = progress_data["remaining"] / months_left
    
    if not has_history:
        impact_pct = 0.0
        impact_pct_clean = 0.0
        impact_message = "Not enough financial data to estimate savings capacity."
        message = "Not enough financial data to estimate savings capacity."
    elif average_savings_capacity <= 0:
        impact_pct = 100.0 if req_monthly > 0 else 0.0
        impact_pct_clean = 100.0 if req_monthly > 0 else 0.0
        impact_message = f"This goal uses {impact_pct:.0f}% of your average monthly savings capacity."
        message = impact_message
    else:
        impact_pct = (req_monthly / average_savings_capacity) * 100.0
        impact_pct_clean = min(100.0, impact_pct)
        impact_message = f"This goal uses {impact_pct:.0f}% of your average monthly savings capacity."
        message = impact_message
    
    return {
        "req_monthly": req_monthly,
        "average_savings_capacity": average_savings_capacity,
        "current_savings_capacity": average_savings_capacity,
        "impact_pct": impact_pct_clean,
        "raw_impact_pct": impact_pct,
        "months_left": months_left,
        "has_history": has_history,
        "active_months": active_months,
        "context_message": context_message,
        "impact_message": impact_message,
        "message": message
    }

def calculate_goal_health(affordability_data: Dict[str, Any], progress_data: Dict[str, Any]) -> Dict[str, Any]:
    if progress_data.get("is_completed"):
        return {
            "status": "GREEN",
            "title": "✓ On Track",
            "message": "You have successfully reached your goal target."
        }
        
    if progress_data.get("is_overdue"):
        return {
            "status": "RED",
            "title": "⚠ At Risk",
            "message": "This goal is past its target date."
        }
        
    if affordability_data.get("has_history") is False:
        return {
            "status": "YELLOW",
            "title": "ℹ Insufficient Data",
            "message": "Not enough financial data to estimate savings capacity."
        }
        
    impact = affordability_data.get("raw_impact_pct", 0.0)
    req = affordability_data.get("req_monthly", 0.0)
    capacity = affordability_data.get("average_savings_capacity", affordability_data.get("current_savings_capacity", 0.0))
    
    if capacity <= 0 or impact > 100:
        return {
            "status": "RED",
            "title": "⚠ At Risk",
            "message": f"Average saving pace will miss the deadline. You need ₹{req:,.0f}/month but your capacity is ₹{capacity:,.0f}."
        }
    elif impact > 50:
        return {
            "status": "YELLOW",
            "title": "⚠ Needs Adjustment",
            "message": f"Increase monthly contribution by ₹{(req - capacity) if req > capacity else 0:,.0f}. This goal uses {impact:.0f}% of savings."
        }
    else:
        return {
            "status": "GREEN",
            "title": "✓ On Track",
            "message": "Your average saving capacity supports this goal."
        }

def calculate_goal_projection(goal, affordability_data: Dict[str, Any], progress_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    projection = []
    
    if progress_data["is_completed"]:
        return [{"month": "Current", "projected_amount": progress_data["saved"]}]
        
    req_monthly = affordability_data["req_monthly"]
    current_saved = progress_data["saved"]
    months_left = affordability_data["months_left"]
    target = progress_data["target"]
    
    display_months = min(6, months_left)
    
    for i in range(1, display_months + 1):
        proj_amt = current_saved + (req_monthly * i)
        if proj_amt >= target:
            proj_amt = target
            projection.append({
                "month": f"Month {i}",
                "projected_amount": proj_amt
            })
            break
            
        projection.append({
            "month": f"Month {i}",
            "projected_amount": proj_amt
        })
            
    if len(projection) > 0 and projection[-1]["projected_amount"] < target and display_months < months_left:
         projection.append({
             "month": f"Month {months_left} (Target)",
             "projected_amount": target
         })
         
    return projection

def build_goal_intelligence(goal, financial_periods: Any) -> Dict[str, Any]:
    progress = calculate_goal_progress(goal)
    affordability = calculate_goal_affordability(goal, financial_periods, progress)
    health = calculate_goal_health(affordability, progress)
    projection = calculate_goal_projection(goal, affordability, progress)
    
    # Extract real income/expense data from the latest period
    if financial_periods is None:
        periods_list = []
    elif isinstance(financial_periods, (list, tuple)):
        periods_list = list(financial_periods)
    else:
        periods_list = [financial_periods]
        
    latest_period = periods_list[-1] if periods_list else None
    total_income = float(getattr(latest_period, 'total_income', 0.0) or 0.0) if latest_period else 0.0
    total_expenses = float(getattr(latest_period, 'total_expenses', 0.0) or 0.0) if latest_period else 0.0
    
    return {
        "goal_id": goal.id,
        "goal_name": goal.goal_name,
        "created_date": goal.created_at,
        "target_date": goal.target_date,
        "progress": progress,
        "affordability": affordability,
        "health": health,
        "projection": projection,
        "total_income": total_income,
        "total_expenses": total_expenses
    }

