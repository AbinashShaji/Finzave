"""
Module: planning/insights.py

Purpose:
Handles goal projections, SIP, and EMI calculations.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from typing import Optional
from planning.services import calculate_loan_affordability

def generate_planning_insight(
    planned_amount: float,
    monthly_savings: float,
    plan_type: str,
    monthly_income: Optional[float] = None
) -> dict:
    """
    Generates a financial insight comparing a planned financial commitment 
    (SIP or EMI) against the user's available monthly savings or income.
    
    For EMI: If monthly_income is provided, evaluates banking FOIR loan affordability.
             Otherwise, evaluates against monthly_savings for backward compatibility.
    For SIP: Evaluates investment affordability against monthly_savings.
    """
    if plan_type == "EMI" and monthly_income is not None:
        return calculate_loan_affordability(
            monthly_income=monthly_income,
            monthly_emi=planned_amount,
            monthly_savings=monthly_savings
        )

    if monthly_savings < 0:
        return {
            "status": "WARNING",
            "message": f"You currently have negative monthly savings. Taking on a new {plan_type} may increase your financial strain."
        }
        
    if monthly_savings == 0:
        return {
            "status": "WARNING",
            "message": f"You currently have no monthly savings available for this {plan_type}."
        }
        
    percentage = (planned_amount / monthly_savings) * 100
    remaining = monthly_savings - planned_amount

    if percentage > 100:
        return {
            "status": "WARNING",
            "message": f"This {plan_type} exceeds your average monthly savings capacity."
        }
    elif percentage >= 80:
        return {
            "status": "WARNING",
            "message": f"This {plan_type} uses {percentage:.0f}% of your average monthly savings. This may reduce your ability to maintain investments and emergency savings."
        }
    else:
        return {
            "status": "SUCCESS",
            "message": f"This {plan_type} uses {percentage:.0f}% of your average monthly savings. Your remaining savings capacity is approximately ₹{remaining:,.0f}."
        }
