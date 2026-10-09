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

def calculate_goal_affordability(goal, current_period: FinancialPeriod, progress_data: Dict[str, Any]) -> Dict[str, Any]:
    today = date.today()
    if progress_data["is_completed"]:
        return {
            "req_monthly": 0.0,
            "current_savings_capacity": current_period.savings if current_period else 0.0,
            "impact_pct": 0.0,
            "raw_impact_pct": 0.0,
            "months_left": 0
        }
        
    target_date = goal.target_date
    months = (target_date.year - today.year) * 12 + target_date.month - today.month
    months_left = max(1, months if target_date >= today else 0)
    
    if progress_data["is_overdue"]:
        months_left = 1 
        
    req_monthly = progress_data["remaining"] / months_left
    current_capacity = current_period.savings if current_period else 0.0
    
    if current_capacity <= 0:
        impact_pct = 100.0 if req_monthly > 0 else 0.0
    else:
        impact_pct = (req_monthly / current_capacity) * 100.0
        
    impact_pct_clean = min(100.0, impact_pct) if current_capacity > 0 else impact_pct
    
    return {
        "req_monthly": req_monthly,
        "current_savings_capacity": current_capacity,
        "impact_pct": impact_pct_clean,
        "raw_impact_pct": impact_pct,
        "months_left": months_left
    }

def calculate_goal_health(affordability_data: Dict[str, Any], progress_data: Dict[str, Any]) -> Dict[str, Any]:
    if progress_data["is_completed"]:
        return {
            "status": "GREEN",
            "title": "✓ On Track",
            "message": "You have successfully reached your goal target."
        }
        
    if progress_data["is_overdue"]:
        return {
            "status": "RED",
            "title": "⚠ At Risk",
            "message": "This goal is past its target date."
        }
        
    impact = affordability_data["raw_impact_pct"]
    req = affordability_data["req_monthly"]
    capacity = affordability_data["current_savings_capacity"]
    
    if capacity <= 0 or impact > 100:
        return {
            "status": "RED",
            "title": "⚠ At Risk",
            "message": f"Current saving pace will miss the deadline. You need ₹{req:,.0f}/month but your capacity is ₹{capacity:,.0f}."
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
            "message": "Your current saving capacity supports this goal."
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

def build_goal_intelligence(goal, current_period: FinancialPeriod) -> Dict[str, Any]:
    progress = calculate_goal_progress(goal)
    affordability = calculate_goal_affordability(goal, current_period, progress)
    health = calculate_goal_health(affordability, progress)
    projection = calculate_goal_projection(goal, affordability, progress)
    
    # Extract real income/expense data from the financial period
    total_income = current_period.total_income if current_period else 0.0
    total_expenses = current_period.total_expenses if current_period else 0.0
    
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

