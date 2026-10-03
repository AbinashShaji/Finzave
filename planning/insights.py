def generate_planning_insight(planned_amount: float, monthly_savings: float, plan_type: str) -> dict:
    """
    Generates a financial insight comparing a planned financial commitment 
    (SIP or EMI) against the user's available monthly savings.
    """
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
            "message": f"This {plan_type} exceeds your current monthly savings capacity."
        }
    elif percentage >= 80:
        return {
            "status": "WARNING",
            "message": f"This {plan_type} uses {percentage:.0f}% of your current savings. This may reduce your ability to maintain investments and emergency savings."
        }
    else:
        return {
            "status": "SUCCESS",
            "message": f"This {plan_type} uses {percentage:.0f}% of your current savings. Your remaining savings capacity is approximately ₹{remaining:,.0f}."
        }
