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
        yearly_amortization = []
        rem_balance = principal
        for y in range(1, years + 1):
            p_paid = monthly_emi * 12
            rem_balance = max(0, rem_balance - p_paid)
            yearly_amortization.append({
                "year": y,
                "principal_paid": round(p_paid, 2),
                "interest_paid": 0,
                "remaining_balance": round(rem_balance, 2)
            })
        return {
            "monthly_emi": monthly_emi,
            "total_interest": 0,
            "total_payment": principal,
            "yearly_amortization": yearly_amortization
        }
        
    r = annual_rate / 12 / 100
    monthly_emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
    total_payment = monthly_emi * n
    total_interest = total_payment - principal
    
    yearly_amortization = []
    rem_balance = principal
    for y in range(1, years + 1):
        year_p_paid = 0
        year_i_paid = 0
        for m in range(12):
            i_paid = rem_balance * r
            p_paid = monthly_emi - i_paid
            year_i_paid += i_paid
            year_p_paid += p_paid
            rem_balance -= p_paid
            
        yearly_amortization.append({
            "year": y,
            "principal_paid": round(year_p_paid, 2),
            "interest_paid": round(year_i_paid, 2),
            "remaining_balance": max(0, round(rem_balance, 2))
        })
    
    return {
        "monthly_emi": monthly_emi,
        "total_interest": total_interest,
        "total_payment": total_payment,
        "yearly_amortization": yearly_amortization
    }
