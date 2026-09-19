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
        return {
            "total_invested": total_invested,
            "est_returns": 0,
            "future_value": total_invested
        }

    i = annual_rate / 12 / 100
    future_value = monthly_investment * (((1 + i) ** n - 1) / i) * (1 + i)
    est_returns = future_value - total_invested
    
    return {
        "total_invested": total_invested,
        "est_returns": est_returns,
        "future_value": future_value
    }
