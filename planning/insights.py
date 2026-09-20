def generate_planning_insight(planned_amount: float, monthly_savings: float, plan_type: str) -> dict:
    """
    Generates a financial insight comparing a planned financial commitment 
    (SIP or EMI) against the user's available monthly savings.
    
    This is a pure deterministic function that does not use AI or ML.
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

    if planned_amount > monthly_savings:
        if plan_type == "EMI":
            return {
                "status": "WARNING",
                "message": "The EMI amount exceeds your current monthly savings capacity."
            }
        else:
            return {
                "status": "WARNING",
                "message": "Based on your current monthly savings, this SIP amount may not be practical."
            }

    return {
        "status": "SUCCESS",
        "message": f"Based on your current savings, this {plan_type} appears manageable."
    }
