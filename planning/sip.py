"""
Module: planning/sip.py

Purpose:
Handles goal projections, SIP, and EMI calculations.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
def calculate_sip(monthly_investment: float, annual_rate: float, years: int) -> dict:
    """
    Calculates the future value of a Systematic Investment Plan (SIP).
    Formula: M = P * ((1 + i)^n - 1) / i * (1 + i)
    where:
    M = Future value
    P = Monthly investment
    i = Monthly interest rate (annual_rate / 12 / 100)
    n = Total number of months (years * 12)
    """
    if monthly_investment <= 0 or years <= 0:
        return {"total_invested": 0, "est_returns": 0, "future_value": 0}
        
    n = years * 12
    total_invested = monthly_investment * n
    
    if annual_rate == 0:
        yearly_breakdown = []
        for y in range(1, years + 1):
            inv = monthly_investment * y * 12
            yearly_breakdown.append({
                "year": y,
                "invested": round(inv, 2),
                "returns": 0,
                "value": round(inv, 2)
            })
        return {
            "total_invested": total_invested,
            "est_returns": 0,
            "future_value": total_invested,
            "yearly_breakdown": yearly_breakdown
        }

    i = annual_rate / 12 / 100
    future_value = monthly_investment * (((1 + i) ** n - 1) / i) * (1 + i)
    est_returns = future_value - total_invested
    
    yearly_breakdown = []
    for y in range(1, years + 1):
        months_passed = y * 12
        inv = monthly_investment * months_passed
        fv = monthly_investment * (((1 + i) ** months_passed - 1) / i) * (1 + i)
        ret = fv - inv
        yearly_breakdown.append({
            "year": y,
            "invested": round(inv, 2),
            "returns": round(ret, 2),
            "value": round(fv, 2)
        })
    
    return {
        "total_invested": total_invested,
        "est_returns": est_returns,
        "future_value": future_value,
        "yearly_breakdown": yearly_breakdown
    }
