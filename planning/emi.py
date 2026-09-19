def calculate_emi(principal: float, annual_rate: float, years: int) -> dict:
    """
    Calculates the Equated Monthly Installment (EMI) for a loan.
    Formula: E = P * r * (1 + r)^n / ((1 + r)^n - 1)
    where:
    E = EMI
    P = Principal loan amount
    r = Monthly interest rate (annual_rate / 12 / 100)
    n = Total number of months (years * 12)
    """
    if principal <= 0 or years <= 0:
        return {"monthly_emi": 0, "total_interest": 0, "total_payment": 0}
        
    n = years * 12
    
    if annual_rate == 0:
        monthly_emi = principal / n
        return {
            "monthly_emi": monthly_emi,
            "total_interest": 0,
            "total_payment": principal
        }
        
    r = annual_rate / 12 / 100
    monthly_emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
    total_payment = monthly_emi * n
    total_interest = total_payment - principal
    
    return {
        "monthly_emi": monthly_emi,
        "total_interest": total_interest,
        "total_payment": total_payment
    }
