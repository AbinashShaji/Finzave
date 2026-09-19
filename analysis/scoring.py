from utils.rule_engine import FinancialPeriod
from typing import List, Dict, Any

def calculate_health_score(current_period: FinancialPeriod, insights: List[Dict[str, Any]]) -> dict:
    """
    Calculates a deterministic Financial Health Score (0-100).
    Returns a dict with 'score', 'status' (Excellent, Good, Fair, Poor), and 'trend_change'.
    """
    score = 50  # Base score
    
    if not current_period:
        return {"score": 0, "status": "No Data", "trend_change": 0}
        
    if current_period and current_period.total_income > 0:
        savings_rate = current_period.savings_rate
        
        if savings_rate is not None:
            if savings_rate >= 0.30:
                score += 25
            elif savings_rate >= 0.20:
                score += 15
            elif savings_rate >= 0.10:
                score += 5
            elif savings_rate < 0:
                score -= 20
        
        # Discretionary spending bonus
        from utils.rule_engine import DISCRETIONARY_CATEGORIES
        if current_period.total_expenses > 0:
            disc_spending = sum(amt for cat, amt in current_period.categories.items() if cat in DISCRETIONARY_CATEGORIES)
            disc_share = disc_spending / current_period.total_expenses
            if disc_share <= 0.20:
                score += 10
            elif disc_share >= 0.40:
                score -= 10
                
    # Modify based on rule engine insights
    for insight in insights:
        if insight.get('severity') == 'SUCCESS':
            score += 5
        elif insight.get('severity') == 'WARNING':
            score -= 10
            
    # Clamp score between 0 and 100
    score = max(0, min(100, int(score)))
    
    if score >= 80:
        status = "Excellent"
    elif score >= 60:
        status = "Good"
    elif score >= 40:
        status = "Fair"
    else:
        status = "Poor"
        
    return {
        "score": score,
        "status": status,
        "trend_change": 0 # to be implemented later if historical comparison is needed
    }
