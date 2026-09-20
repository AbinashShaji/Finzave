from typing import List, Dict
from .rules import RECOMMENDATION_MAPPINGS

def generate_recommendations(insights: List[Dict], prepared_goals: List[Dict], metrics: Dict, health_score: Dict) -> List[Dict]:
    """
    Transforms deterministic signals (insights, goals, metrics, health_score) into actionable recommendations.
    This is a pure function. It does not modify inputs or create new rules.
    """
    recommendations = []
    seen_sources = set()

    # 1. Map Rule Engine Insights
    for insight in insights:
        rule_id = insight.get("rule_id")
        if rule_id and rule_id in RECOMMENDATION_MAPPINGS:
            if rule_id not in seen_sources:
                recommendations.append(RECOMMENDATION_MAPPINGS[rule_id])
                seen_sources.add(rule_id)

    # 2. Map Prepared Goal States
    # We do not recalculate months_left or req_monthly. We use the supplied data.
    has_overdue_goal = False
    for goal in prepared_goals:
        if goal.get("status") == "OVERDUE" and "GOAL_OVERDUE" not in seen_sources:
            recommendations.append({
                "source": "GOAL_OVERDUE",
                "category": "PLANNING",
                "priority": "HIGH",
                "title": "Review Overdue Goals",
                "message": f"Your goal '{goal.get('goal_name')}' is past its target date. Consider adjusting the target date or increasing your monthly savings."
            })
            seen_sources.add("GOAL_OVERDUE")
            has_overdue_goal = True
            
    # Positive reinforcement if goals are on track and there's surplus
    total_savings = metrics.get('current_period', {}).get('total_savings', 0)
    total_req_monthly = sum(g.get('req_monthly', 0) for g in prepared_goals if g.get('status') == 'ACTIVE')
    
    if prepared_goals and not has_overdue_goal and total_savings > total_req_monthly:
        if "GOAL_SURPLUS" not in seen_sources:
            recommendations.append({
                "source": "GOAL_SURPLUS",
                "category": "PLANNING",
                "priority": "LOW",
                "title": "Allocate Surplus Savings",
                "message": "You are saving more than your active goals require. Consider using the Planning calculator to invest this surplus."
            })
            seen_sources.add("GOAL_SURPLUS")

    # 3. Contextual Health Score
    # We only use predefined boundaries (e.g. category="Critical" as defined in scoring.py)
    hs_category = health_score.get("category", "")
    if hs_category == "Critical" and "HS_CRITICAL" not in seen_sources:
        recommendations.append({
            "source": "HS_CRITICAL",
            "category": "EMERGENCY",
            "priority": "HIGH",
            "title": "Critical Financial Health",
            "message": "Your financial health score is critical based on the FinZave algorithm. Prioritize halting non-essential spending."
        })
        seen_sources.add("HS_CRITICAL")

    # Sort recommendations by priority (HIGH -> MEDIUM -> LOW)
    priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.get("priority", "LOW"), 3))

    return recommendations
