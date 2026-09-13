import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Core thresholds from the project specification
LOW_SAVINGS_RATE = 0.20
POSITIVE_SAVINGS_RATE = 0.20
TREND_CHANGE_PERCENTAGE = 0.05
HIGH_CATEGORY_PERCENTAGE = 0.30
CATEGORY_DEVIATION_FACTOR = 1.5
DISCRETIONARY_SPENDING_THRESHOLD = 0.30
CONSECUTIVE_PERIODS_FOR_TREND = 3
MIN_PERIODS_FOR_COMPARISON = 2
SIP_HIGH_COMMITMENT_RATIO = 0.75
EMI_HIGH_COMMITMENT_RATIO = 0.75

DISCRETIONARY_CATEGORIES = {
    'Entertainment', 'Shopping', 'Dining', 'Travel', 'Subscriptions', 'Leisure'
}

class FinancialPeriod:
    def __init__(self, period_id: str, fixed_income: float, variable_income: float, expenses: List[Dict[str, Any]]):
        self.period_id = period_id
        self.fixed_income = fixed_income
        self.variable_income = variable_income
        self.total_income = fixed_income + variable_income
        
        self.expenses = expenses
        self.total_expenses = sum(e.get('amount', 0.0) for e in expenses)
        
        # Calculate Savings
        self.savings = self.total_income - self.total_expenses
        
        # Calculate Savings Rate
        if self.total_income > 0:
            self.savings_rate = self.savings / self.total_income
        else:
            self.savings_rate = None
            
        # Category aggregation
        self.categories = {}
        for e in expenses:
            cat = e.get('category', 'Others')
            amt = e.get('amount', 0.0)
            self.categories[cat] = self.categories.get(cat, 0.0) + amt

def percentage_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None
    return ((current - previous) / previous)

def classify_trend(change: float) -> str:
    if change < -TREND_CHANGE_PERCENTAGE:
        return "DECREASING"
    elif change > TREND_CHANGE_PERCENTAGE:
        return "INCREASING"
    else:
        return "STABLE"

def evaluate_rules(periods: List[FinancialPeriod]) -> List[Dict[str, Any]]:
    insights = []
    
    if not periods:
        return insights
        
    # Sort chronologically assumed (oldest to newest)
    current_period = periods[-1]
    
    # Needs at least one period for single-period rules
    _evaluate_rb03_low_savings_rate(current_period, insights)
    _evaluate_rb06_high_discretionary(current_period, insights)
    
    if len(periods) >= MIN_PERIODS_FOR_COMPARISON:
        _evaluate_rb05_expenses_vs_income(periods[-2], current_period, insights)
        _evaluate_rb08_positive_savings(periods[-2], current_period, insights)
        _evaluate_rb02_and_rb07_category_deviation(periods, insights)
        
    if len(periods) >= CONSECUTIVE_PERIODS_FOR_TREND:
        _evaluate_rb01_increasing_expenses(periods, insights)
        _evaluate_rb04_declining_savings(periods, insights)
        
    return insights

def _evaluate_rb01_increasing_expenses(periods: List[FinancialPeriod], insights: List[Dict]):
    """RB-01: Increasing Expenses"""
    # Needs 3 consecutive comparable periods, meaning 4 periods in total (3 transitions) OR 3 transitions over 4 periods.
    # The specification says: "at least 3 comparable consecutive periods exist AND each consecutive period is classified as INCREASING"
    # To have 3 comparable consecutive periods, you need 4 actual periods (p1->p2, p2->p3, p3->p4).
    # Wait, example: Jan(20k)->Feb(23k)->Mar(27k). This has 2 transitions: Jan->Feb, Feb->Mar.
    # "at least 3 comparable consecutive periods exist". Jan, Feb, Mar are 3 periods.
    
    recent_periods = periods[-3:]
    if len(recent_periods) < 3:
        return
        
    change1 = percentage_change(recent_periods[1].total_expenses, recent_periods[0].total_expenses)
    change2 = percentage_change(recent_periods[2].total_expenses, recent_periods[1].total_expenses)
    
    if change1 is not None and change2 is not None:
        t1 = classify_trend(change1)
        t2 = classify_trend(change2)
        if t1 == "INCREASING" and t2 == "INCREASING":
            insights.append({
                "rule_id": "RB-01",
                "group": "EXPENSE_PRESSURE",
                "severity": "WARNING",
                "message": "Your expenses have been increasing consistently over recent periods."
            })

def _evaluate_rb02_and_rb07_category_deviation(periods: List[FinancialPeriod], insights: List[Dict]):
    """RB-02 & RB-07: Personalised Category Spending Deviation"""
    current_period = periods[-1]
    historical_periods = periods[:-1]
    
    if current_period.total_expenses == 0:
        return
        
    for category, current_amount in current_period.categories.items():
        current_share = current_amount / current_period.total_expenses
        
        # Calculate historical average share
        historical_shares = []
        for hp in historical_periods:
            if hp.total_expenses > 0:
                h_amt = hp.categories.get(category, 0.0)
                historical_shares.append(h_amt / hp.total_expenses)
                
        if not historical_shares:
            continue
            
        historical_avg_share = sum(historical_shares) / len(historical_shares)
        
        if historical_avg_share > 0:
            deviation_ratio = current_share / historical_avg_share
            
            if current_share >= HIGH_CATEGORY_PERCENTAGE and deviation_ratio >= CATEGORY_DEVIATION_FACTOR:
                insights.append({
                    "rule_id": "RB-02",
                    "group": "SPENDING_CONCENTRATION",
                    "severity": "INFO",
                    "message": f"{category} represents {current_share*100:.1f}% of your spending this month, compared with your usual average of about {historical_avg_share*100:.1f}%."
                })
            elif deviation_ratio >= CATEGORY_DEVIATION_FACTOR:
                insights.append({
                    "rule_id": "RB-07",
                    "group": "SPENDING_CONCENTRATION",
                    "severity": "INFO",
                    "message": f"Your spending in {category} is unusually high compared to your historical average."
                })

def _evaluate_rb03_low_savings_rate(current_period: FinancialPeriod, insights: List[Dict]):
    """RB-03: Low Savings Rate"""
    if current_period.total_income > 0 and current_period.savings_rate is not None:
        if current_period.savings_rate < LOW_SAVINGS_RATE:
            insights.append({
                "rule_id": "RB-03",
                "group": "SAVINGS",
                "severity": "WARNING",
                "message": "Your current savings rate is below the FinZave analysis threshold."
            })

def _evaluate_rb04_declining_savings(periods: List[FinancialPeriod], insights: List[Dict]):
    """RB-04: Declining Savings"""
    recent_periods = periods[-3:]
    if len(recent_periods) < 3:
        return
        
    change1 = percentage_change(recent_periods[1].savings, recent_periods[0].savings)
    change2 = percentage_change(recent_periods[2].savings, recent_periods[1].savings)
    
    if change1 is not None and change2 is not None:
        t1 = classify_trend(change1)
        t2 = classify_trend(change2)
        if t1 == "DECREASING" and t2 == "DECREASING":
            insights.append({
                "rule_id": "RB-04",
                "group": "SAVINGS",
                "severity": "WARNING",
                "message": "Your savings have been declining over recent periods."
            })

def _evaluate_rb05_expenses_vs_income(prev: FinancialPeriod, curr: FinancialPeriod, insights: List[Dict]):
    """RB-05: Expenses Growing Faster Than Income"""
    income_growth = percentage_change(curr.total_income, prev.total_income)
    expense_growth = percentage_change(curr.total_expenses, prev.total_expenses)
    
    if income_growth is not None and expense_growth is not None:
        if expense_growth > 0 and expense_growth > income_growth:
            insights.append({
                "rule_id": "RB-05",
                "group": "EXPENSE_PRESSURE",
                "severity": "WARNING",
                "message": f"Your expenses rose by {expense_growth*100:.1f}% while your income rose by {income_growth*100:.1f}%."
            })

def _evaluate_rb06_high_discretionary(current_period: FinancialPeriod, insights: List[Dict]):
    """RB-06: High Discretionary Spending"""
    if current_period.total_expenses > 0:
        disc_spending = sum(amount for cat, amount in current_period.categories.items() if cat in DISCRETIONARY_CATEGORIES)
        disc_share = disc_spending / current_period.total_expenses
        
        if disc_share >= DISCRETIONARY_SPENDING_THRESHOLD:
            insights.append({
                "rule_id": "RB-06",
                "group": "SPENDING_CONCENTRATION",
                "severity": "INFO",
                "message": "A significant portion of your expenses is going toward discretionary categories."
            })

def _evaluate_rb08_positive_savings(prev: FinancialPeriod, curr: FinancialPeriod, insights: List[Dict]):
    """RB-08: Positive Savings Pattern"""
    if curr.total_income > 0 and curr.savings_rate is not None:
        if curr.savings_rate >= POSITIVE_SAVINGS_RATE:
            savings_growth = percentage_change(curr.savings, prev.savings)
            if savings_growth is not None:
                trend = classify_trend(savings_growth)
                if trend in ["STABLE", "INCREASING"]:
                    insights.append({
                        "rule_id": "RB-08",
                        "group": "SAVINGS",
                        "severity": "SUCCESS",
                        "message": "Your savings pattern is currently positive based on the FinZave analysis threshold."
                    })
