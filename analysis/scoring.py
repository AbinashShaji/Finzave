import logging
from typing import List, Dict, Any, Optional
from utils.rule_engine import FinancialPeriod

logger = logging.getLogger(__name__)

BASE_SCORE = 50

# Maintainable impact map
HEALTH_SCORE_IMPACTS = {
    "RB-01": -10,
    "RB-02": -8,
    "RB-03": -15,
    "RB-04": -10,
    "RB-05": -15,
    "RB-06": -10,
    "RB-07": -8,
    "RB-08": 10,
    "RB-09": 0
}

def normalize_score(score: int) -> int:
    """Clamps the score between 0 and 100."""
    return max(0, min(100, score))

def get_score_category(score: int) -> str:
    """Returns the descriptive category based on the health score."""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 50:
        return "Moderate"
    elif score >= 25:
        return "Needs Attention"
    else:
        return "Critical"

def apply_rule_impacts(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Applies the impacts for the provided rule insights.
    Implements duplicate behaviour protection (e.g. groups related insights 
    and applies maximum relevant impact).
    """
    adjustments = []
    
    # Group by the 'group' field in insights (e.g. SPENDING_CONCENTRATION)
    # We want to apply only the maximum absolute impact per group to avoid double-penalizing.
    groups_processed: Dict[str, Dict[str, Any]] = {}
    
    for insight in insights:
        rule_id = insight.get("rule_id")
        group = insight.get("group")
        
        impact = HEALTH_SCORE_IMPACTS.get(rule_id, 0)
        
        # Only process known rules with non-zero impact (or we include 0 impact for explainability?
        # The spec says RB-09 is 0, let's include it for completeness if needed, but usually 
        # adjustments are for actual impact. The spec says "generate explainable adjustments").
        # We will process it.
        
        # Duplicate behaviour protection:
        if group:
            if group not in groups_processed:
                groups_processed[group] = {
                    "rule_id": rule_id,
                    "impact": impact,
                    "reason": insight.get("message", f"Rule {rule_id} triggered"),
                    "group": group
                }
            else:
                # Keep the one with the maximum absolute impact
                current_max_impact = groups_processed[group]["impact"]
                if abs(impact) > abs(current_max_impact):
                    groups_processed[group] = {
                        "rule_id": rule_id,
                        "impact": impact,
                        "reason": insight.get("message", f"Rule {rule_id} triggered"),
                        "group": group
                    }
        else:
            # If no group, just append directly (though rule_engine adds group to all)
            adjustments.append({
                "rule_id": rule_id,
                "impact": impact,
                "reason": insight.get("message", f"Rule {rule_id} triggered"),
                "evidence": {}
            })
            
    # Move deduplicated grouped insights into adjustments
    for group_data in groups_processed.values():
        adjustments.append({
            "rule_id": group_data["rule_id"],
            "impact": group_data["impact"],
            "reason": group_data["reason"],
            "evidence": {}
        })
        
    return adjustments

def generate_explanation(adjustments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Formats the final list of adjustments for the UI.
    (Currently pass-through, but acts as a clear separation for explanation building)
    """
    return adjustments

def calculate_health_score(periods: List[FinancialPeriod], metrics_has_data: bool, insights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates the final Health Score deterministically.
    """
    if not metrics_has_data:
        return {
            "status": "INSUFFICIENT_DATA",
            "score": None,
            "category": None,
            "adjustments": []
        }
        
    adjustments = apply_rule_impacts(insights)
    explained_adjustments = generate_explanation(adjustments)
    
    total_impact = sum(adj["impact"] for adj in explained_adjustments)
    final_score = normalize_score(BASE_SCORE + total_impact)
    category = get_score_category(final_score)
    
    return {
        "status": "SUCCESS",
        "score": final_score,
        "category": category,
        "adjustments": explained_adjustments
    }
