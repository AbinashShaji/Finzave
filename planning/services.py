"""
Module: planning/services.py

Purpose:
Handles financial planning capacity calculation, SIP recommendations,
and planning intelligence using historical average monthly savings.

Flow:
User Request -> Route Handler -> Planning Services -> Database / Rule Engine
"""
from typing import Any, Dict, List, Optional
from utils.rule_engine import FinancialPeriod

def calculate_planning_capacity(financial_periods: Any) -> Dict[str, Any]:
    """
    Calculates historical average monthly savings capacity for the planning module.
    
    Formula:
    average_monthly_savings_capacity = 
        sum(monthly savings of active periods) / number of active periods
        
    Active periods:
    - Excludes 'no_data' periods
    - Excludes periods with income == 0 and expenses == 0
    """
    # Normalize input into a list of periods
    if financial_periods is None:
        periods_list = []
    elif isinstance(financial_periods, (list, tuple)):
        periods_list = list(financial_periods)
    else:
        periods_list = [financial_periods]
        
    # Filter active periods (exclude no_data periods)
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
    
    # Extract latest active income for backward compatibility
    latest_period = active_periods[-1] if active_periods else (periods_list[-1] if periods_list else None)
    latest_income = float(getattr(latest_period, 'total_income', 0.0) or 0.0) if latest_period else 0.0

    if active_months > 0:
        has_history = True
        total_savings = 0.0
        total_income = 0.0
        for p in active_periods:
            if hasattr(p, 'total_income') and hasattr(p, 'total_expenses') and p.total_income is not None and p.total_expenses is not None:
                m_savings = float(p.total_income) - float(p.total_expenses)
                m_income = float(p.total_income)
            elif hasattr(p, 'savings') and p.savings is not None:
                m_savings = float(p.savings)
                m_income = float(getattr(p, 'total_income', None) or getattr(p, 'income', 0.0) or 0.0)
            else:
                m_savings = 0.0
                m_income = float(getattr(p, 'total_income', None) or getattr(p, 'income', 0.0) or 0.0)
            total_savings += m_savings
            total_income += m_income
            
        average_savings_capacity = total_savings / active_months
        average_monthly_income = total_income / active_months
        month_word = "month" if active_months == 1 else "months"
        context_message = f"Based on {active_months} {month_word} of financial history"
        capacity_message = "Calculated using your average monthly savings"
        
        if active_months < 3:
            is_limited_history = True
            history_note = "Limited financial history. Planning estimates may change as more data is recorded."
        else:
            is_limited_history = False
            history_note = ""
            
        if average_savings_capacity > 0:
            suggested_sip_min = round(average_savings_capacity * 0.30, 2)
            suggested_sip_max = round(average_savings_capacity * 0.50, 2)
        else:
            suggested_sip_min = 0.0
            suggested_sip_max = 0.0
    else:
        has_history = False
        is_limited_history = False
        average_savings_capacity = 0.0
        average_monthly_income = 0.0
        context_message = "Not enough financial data to estimate planning capacity."
        capacity_message = "Calculated using your average monthly savings"
        history_note = "Not enough financial data to estimate planning capacity."
        suggested_sip_min = 0.0
        suggested_sip_max = 0.0

    return {
        "average_savings_capacity": average_savings_capacity,
        "current_savings_capacity": average_savings_capacity,
        "average_monthly_income": average_monthly_income,
        "average_income": average_monthly_income,
        "active_months": active_months,
        "has_history": has_history,
        "context_message": context_message,
        "capacity_message": capacity_message,
        "history_note": history_note,
        "is_limited_history": is_limited_history,
        "savings": average_savings_capacity,
        "income": average_monthly_income if average_monthly_income > 0 else latest_income,
        "suggested_sip_min": suggested_sip_min,
        "suggested_sip_max": suggested_sip_max,
        "message": context_message
    }


def calculate_loan_affordability(
    monthly_income: Optional[float] = None,
    monthly_emi: Optional[float] = None,
    monthly_savings: Optional[float] = None,
    *,
    income: Optional[float] = None,
    emi: Optional[float] = None
) -> Dict[str, Any]:
    """
    Evaluates loan affordability using realistic banking standards:
    FOIR (Fixed Obligation to Income Ratio)
    
    Formula:
    FOIR = (Monthly EMI / Monthly Income) * 100
    
    Banking Risk Tiers:
    - < 40%: Healthy
    - 40% - 50%: Moderate
    - 50% - 60%: Risky
    - > 60%: High Risk
    """
    if income is not None:
        monthly_income = income
    if emi is not None:
        monthly_emi = emi

    inc = float(monthly_income or 0.0)
    e = float(monthly_emi or 0.0)
    sav = float(monthly_savings) if monthly_savings is not None else None

    if inc <= 0:
        foir = 100.0 if e > 0 else 0.0
        risk_level = "High Risk" if e > 0 else "Healthy"
        status = "WARNING" if e > 0 else "SUCCESS"
        display_risk = "High" if e > 0 else "Healthy"
        message = (
            "You currently have no recorded monthly income. Taking on an EMI may create financial stress."
            if e > 0 else
            "No loan commitment specified."
        )
        reason = (
            "No recorded monthly income to service this loan."
            if e > 0 else
            "No EMI commitment."
        )
        remaining_savings = (sav - e) if sav is not None else None
        return {
            "income": round(inc, 2),
            "emi": round(e, 2),
            "foir": foir,
            "emi_ratio": foir,
            "risk_level": risk_level,
            "risk": risk_level,
            "display_risk": display_risk,
            "status": status,
            "message": message,
            "reason": reason,
            "monthly_income": round(inc, 2),
            "monthly_emi": round(e, 2),
            "monthly_savings": sav,
            "remaining_savings": remaining_savings
        }

    foir = round((e / inc) * 100, 1)
    remaining_savings = (sav - e) if sav is not None else None

    if foir < 40.0:
        risk_level = "Healthy"
        display_risk = "Healthy"
        status = "SUCCESS"
        message = f"Your EMI uses {round(foir)}% of your average monthly income. This loan appears manageable based on your current cash flow."
        reason = "EMI is well within safe banking limits (< 40% of income)."
    elif foir <= 50.0:
        risk_level = "Moderate"
        display_risk = "Moderate"
        status = "WARNING"
        message = f"Your EMI uses {round(foir)}% of your income. Consider maintaining an emergency buffer before committing."
        reason = "EMI consumes a moderate share of your income (40% - 50%)."
    elif foir <= 60.0:
        risk_level = "Risky"
        display_risk = "Risky"
        status = "WARNING"
        message = f"Your EMI uses {round(foir)}% of your income. This repayment may significantly reduce your monthly financial flexibility."
        reason = "EMI is high relative to your income (50% - 60%)."
    else:
        risk_level = "High Risk"
        display_risk = "High"
        status = "WARNING"
        message = f"Your EMI consumes {round(foir)}% of your average monthly income. This loan may create financial stress."
        reason = "EMI consumes most of your monthly income."

    return {
        "income": round(inc, 2),
        "emi": round(e, 2),
        "foir": foir,
        "emi_ratio": foir,
        "risk_level": risk_level,
        "risk": risk_level,
        "display_risk": display_risk,
        "status": status,
        "message": message,
        "reason": reason,
        "monthly_income": round(inc, 2),
        "monthly_emi": round(e, 2),
        "monthly_savings": sav,
        "remaining_savings": remaining_savings
    }

