"""
Module: analysis/services.py

Purpose:
Performs algorithmic health scoring and complex financial analysis.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from typing import List, Dict, Any, Optional
from utils.rule_engine import FinancialPeriod, percentage_change


# ---------------------------------------------------------------------------
# OVERVIEW (Current Month)
# ---------------------------------------------------------------------------

def build_overview(periods: List[FinancialPeriod]) -> Dict[str, Any]:
    """
    Builds the current-month overview with category-level comparison against
    the previous month, savings-impact insights, and narrative.
    Consumes only FinancialPeriod data — no database queries.
    """
    if not periods:
        return {"has_data": False}

    has_any_data = any((p.total_income > 0 or p.total_expenses > 0) for p in periods)
    if not has_any_data:
        return {"has_data": False}

    current = periods[-1]
    prev = periods[-2] if len(periods) >= 2 else None

    # --- Category breakdown with comparison ---
    category_breakdown = []
    all_cats = set(current.categories.keys())
    if prev:
        all_cats = all_cats.union(prev.categories.keys())

    for cat in sorted(all_cats):
        curr_amt = current.categories.get(cat, 0.0)
        prev_amt = prev.categories.get(cat, 0.0) if prev else 0.0
        diff = curr_amt - prev_amt if current.status != "incomplete" else None
        pct_change = percentage_change(curr_amt, prev_amt) if prev and current.status != "incomplete" else None
        pct_of_income = (curr_amt / current.total_income * 100) if current.total_income > 0 and current.status != "incomplete" else 0.0
        is_new = prev is not None and prev_amt == 0.0 and curr_amt > 0.0 and current.status != "incomplete"

        category_breakdown.append({
            "category": cat,
            "current": curr_amt,
            "previous": prev_amt,
            "diff": diff,
            "change_pct": pct_change,
            "pct_of_income": pct_of_income,
            "is_new": is_new,
        })

    category_breakdown.sort(key=lambda x: x["current"], reverse=True)

    # --- Savings Impact Analysis: detailed per-category insights ---
    savings_insights = []
    FIXED_ESSENTIAL_CATEGORIES = {'Rent & Housing', 'EMI', 'Insurance'}
    if current.status == "incomplete":
        savings_insights.append("Your expense data for this month is incomplete. Savings impact will be calculated after transactions are added.")
    elif prev:
        savings_diff = current.savings - prev.savings
        income_diff = current.total_income - prev.total_income

        # Largest expense contextual insight
        if category_breakdown and category_breakdown[0]["current"] > 0:
            top = category_breakdown[0]
            top_cat = top["category"]
            top_amt = top["current"]
            top_prev = top["previous"]
            is_fixed = top_cat in FIXED_ESSENTIAL_CATEGORIES
            exp_type = "fixed" if is_fixed else "variable"
            if top_prev > 0 and abs(top_amt - top_prev) <= top_prev * 0.05:
                savings_insights.append(
                    f"{top_cat} is your largest expense at ₹{top_amt:,.0f}/month. This remains consistent with previous months and is not increasing."
                )
            elif top_amt > top_prev:
                savings_insights.append(
                    f"{top_cat} is your largest expense at ₹{top_amt:,.0f}/month (increased from ₹{top_prev:,.0f} last month). As a {exp_type} expense, review if this can be optimized."
                )
            else:
                savings_insights.append(
                    f"{top_cat} is your largest expense at ₹{top_amt:,.0f}/month (reduced from ₹{top_prev:,.0f} last month)."
                )

        # All categories that moved by ≥ ₹1, sorted by absolute change (biggest movers first)
        changed_cats = sorted(
            [e for e in category_breakdown if abs(e["diff"]) >= 1],
            key=lambda x: abs(x["diff"]),
            reverse=True,
        )

        for entry in changed_cats:
            cat = entry["category"]
            diff = entry["diff"]
            pct_of_income = entry["pct_of_income"]
            curr_amt = entry["current"]
            prev_amt = entry["previous"]

            # Primary sentence: ₹ change + % of income consumed
            if diff > 0:
                sentence = (
                    f"{cat} spending increased by ₹{diff:,.0f}, "
                    f"using {pct_of_income:.0f}% of your monthly income."
                )
                if abs(savings_diff) >= 1:
                    contribution_pct = diff / abs(savings_diff) * 100
                    if 10 <= contribution_pct <= 150:
                        sentence += (
                            f" This accounts for approximately {contribution_pct:.0f}% "
                            f"of the overall change in your savings."
                        )
            else:
                if curr_amt == 0 and prev_amt > 0:
                    sentence = f"No {cat} spending recorded this month (previously ₹{prev_amt:,.0f})."
                else:
                    sentence = (
                        f"{cat} spending reduced by ₹{abs(diff):,.0f}, "
                        f"now using {pct_of_income:.0f}% of your monthly income."
                    )
                if abs(savings_diff) >= 1:
                    contribution_pct = abs(diff) / abs(savings_diff) * 100
                    if 10 <= contribution_pct <= 150:
                        sentence += (
                            f" This reduction accounts for approximately {contribution_pct:.0f}% "
                            f"of the overall change in your savings."
                        )

            savings_insights.append(sentence)

        # Income movement if significant
        if abs(income_diff) >= 1:
            if income_diff > 0:
                savings_insights.append(
                    f"Your income was ₹{income_diff:,.0f} higher than last month, "
                    f"directly expanding your savings capacity."
                )
            else:
                savings_insights.append(
                    f"Your income was ₹{abs(income_diff):,.0f} lower than last month, "
                    f"compressing your savings capacity."
                )

    # --- Narrative ---
    narrative_title = "Welcome to your financial overview."
    narrative_body = "We don't have enough data yet to compare your spending against previous months. Keep adding transactions!"

    if current.status == "incomplete":
        narrative_title = "Your financial tracking is incomplete."
        narrative_body = "You have recorded income but no expenses yet. Add your expenses to generate an accurate spending analysis."
    elif prev:
        savings_diff = current.savings - prev.savings
        if savings_diff > 0:
            narrative_title = f"Your savings increased by ₹{savings_diff:,.0f} this month."
            top_decreases = [e for e in category_breakdown if e["diff"] < -1]
            top_decreases.sort(key=lambda x: x["diff"])
            if top_decreases:
                details = " and ".join(
                    [f"{c['category']} spending decreased by ₹{abs(c['diff']):,.0f}" for c in top_decreases[:2]]
                )
                narrative_body = f"{details.capitalize()}. These were the main contributors to the improvement."
            else:
                narrative_body = "This improvement was driven by an overall reduction in expenses or an increase in income."
        elif savings_diff < 0:
            narrative_title = f"Your savings fell by ₹{abs(savings_diff):,.0f} this month."
            top_increases = [e for e in category_breakdown if e["diff"] > 1]
            top_increases.sort(key=lambda x: x["diff"], reverse=True)
            if top_increases:
                details = " and ".join(
                    [f"{c['category']} spending increased by ₹{c['diff']:,.0f}" for c in top_increases[:2]]
                )
                narrative_body = f"{details.capitalize()}. These were the main contributors to the decline."
            else:
                narrative_body = "This decline was driven by an overall increase in expenses or a decrease in income."
        else:
            narrative_title = "Your savings remained the same this month."
            narrative_body = "Your financial behaviour was very consistent with last month."

    # --- Trends (for vs-previous-month badges) ---
    trends = {
        "income_change": None,
        "expense_change": None,
        "savings_change": None,
    }
    if prev and current.status != "incomplete":
        ic = percentage_change(current.total_income, prev.total_income)
        ec = percentage_change(current.total_expenses, prev.total_expenses)
        sc = percentage_change(current.savings, prev.savings)
        trends["income_change"] = (ic * 100) if ic is not None else 0.0
        trends["expense_change"] = (ec * 100) if ec is not None else 0.0
        trends["savings_change"] = (sc * 100) if sc is not None else 0.0

    return {
        "has_data": True,
        "is_incomplete": current.status == "incomplete",
        "current_month": current.period_id,
        "income": current.total_income,
        "expenses": current.total_expenses,
        "savings": current.savings,
        "savings_rate": current.savings_rate if current.savings_rate is not None else 0.0,
        "trends": trends,
        "categories": current.categories,
        "category_breakdown": category_breakdown,
        "savings_insights": savings_insights,
        "narrative_title": narrative_title,
        "narrative_body": narrative_body,
        "has_comparison": prev is not None,
    }


# ---------------------------------------------------------------------------
# MONTHLY ANALYSIS
# ---------------------------------------------------------------------------

def _detect_patterns(periods: List[FinancialPeriod]) -> List[str]:
    """Detects behavioural patterns across 3+ periods with actionable metrics."""
    patterns = []
    if len(periods) < 3:
        return patterns

    import calendar

    # Consecutive savings improvement
    consecutive_savings_up = 0
    for i in range(1, len(periods)):
        if periods[i].savings > periods[i - 1].savings:
            consecutive_savings_up += 1
        else:
            consecutive_savings_up = 0

    if consecutive_savings_up >= 2:
        saved_gain = periods[-1].savings - periods[-1 - consecutive_savings_up].savings
        patterns.append(
            f"Your savings improved for {consecutive_savings_up + 1} consecutive months, "
            f"growing by ₹{saved_gain:,.0f} over this period."
        )

    # Consecutive savings decline
    consecutive_savings_down = 0
    for i in range(1, len(periods)):
        if periods[i].savings < periods[i - 1].savings:
            consecutive_savings_down += 1
        else:
            consecutive_savings_down = 0

    if consecutive_savings_down >= 2:
        saved_loss = periods[-1 - consecutive_savings_down].savings - periods[-1].savings
        patterns.append(
            f"Your savings declined for {consecutive_savings_down + 1} consecutive months, "
            f"dropping by ₹{saved_loss:,.0f} over this period."
        )

    # Category spending trends for last 3 months
    recent = periods[-3:]
    cats = set()
    for p in recent:
        cats.update(p.categories.keys())

    first_period = periods[0]
    first_month_name = "the start of the period"
    if "-" in first_period.period_id:
        try:
            m_idx = int(first_period.period_id.split("-")[1])
            first_month_name = calendar.month_name[m_idx]
        except Exception:
            pass

    for cat in sorted(cats):
        m1 = recent[0].categories.get(cat, 0.0)
        m2 = recent[1].categories.get(cat, 0.0)
        m3 = recent[2].categories.get(cat, 0.0)

        if m3 < m2 < m1 and m1 > 0:
            first_amt = first_period.categories.get(cat, 0.0)
            if first_amt > m3:
                saved_vs_start = first_amt - m3
                patterns.append(
                    f"{cat} spending decreased consistently for 3 months, reducing expenses by ₹{saved_vs_start:,.0f} compared with {first_month_name}. This contributed to your improved savings rate."
                )
            else:
                saved_recent = m1 - m3
                patterns.append(
                    f"{cat} spending decreased consistently for 3 months, reducing expenses by ₹{saved_recent:,.0f} over the last quarter. This contributed to your improved savings rate."
                )
        elif m3 > m2 > m1 and m1 > 0:
            increased_recent = m3 - m1
            patterns.append(
                f"{cat} spending increased consistently for 3 months (up by ₹{increased_recent:,.0f}). Monitor this category to prevent cash flow strain."
            )

    # Consistently high expense months
    avg_expense = sum(p.total_expenses for p in periods) / len(periods) if periods else 0
    if avg_expense > 0:
        recent_period = periods[-1]
        if recent_period.total_expenses > avg_expense * 1.3:
            patterns.append(
                f"This month's expenses are {((recent_period.total_expenses / avg_expense - 1) * 100):.0f}% above your average."
            )

    return patterns


def build_monthly_analysis(periods: List[FinancialPeriod]) -> Dict[str, Any]:
    """
    Builds multi-month comparison data including per-month breakdown,
    averages, best/worst months, category changes, recurring income analysis, and patterns.
    """
    if len(periods) < 2:
        return {"has_data": False}

    # --- Per-month data ---
    months_data = []
    for p in periods:
        rate = (p.savings_rate * 100) if p.savings_rate is not None else 0.0
        months_data.append({
            "period": p.period_id,
            "income": p.total_income,
            "fixed_income": p.fixed_income,
            "variable_income": p.variable_income,
            "expenses": p.total_expenses,
            "savings": p.savings,
            "savings_rate": rate,
        })

    # --- Averages ---
    avg_income = sum(p.total_income for p in periods) / len(periods)
    avg_expenses = sum(p.total_expenses for p in periods) / len(periods)
    avg_savings = sum(p.savings for p in periods) / len(periods)

    # --- Best / Worst months ---
    best_month = max(periods, key=lambda p: p.savings)
    worst_month = min(periods, key=lambda p: p.savings)

    # --- Month-over-month changes for the latest two ---
    curr = periods[-1]
    prev = periods[-2]
    income_change = percentage_change(curr.total_income, prev.total_income) if curr.status != "incomplete" else None
    expense_change = percentage_change(curr.total_expenses, prev.total_expenses) if curr.status != "incomplete" else None
    savings_change = percentage_change(curr.savings, prev.savings) if curr.status != "incomplete" else None

    # --- Category comparison across all months ---
    all_cats: set = set()
    for p in periods:
        all_cats.update(p.categories.keys())

    # Build category matrix
    category_totals: Dict[str, float] = {}
    for cat in all_cats:
        category_totals[cat] = sum(p.categories.get(cat, 0.0) for p in periods)

    top_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)[:8]

    category_comparison = []
    for cat, total in top_categories:
        first_val = periods[0].categories.get(cat, 0.0)
        last_val = periods[-1].categories.get(cat, 0.0)
        diff = last_val - first_val
        change_pct = percentage_change(last_val, first_val)
        monthly_values = [p.categories.get(cat, 0.0) for p in periods]
        category_comparison.append({
            "category": cat,
            "total": total,
            "first_month": first_val,
            "last_month": last_val,
            "diff": diff,
            "change_pct": change_pct,
            "monthly_values": monthly_values,
            "is_zero_spending": (last_val == 0.0 and first_val > 0.0)
        })

    # --- Chart data ---
    chart_data = {
        "labels": [p.period_id for p in periods],
        "income": [p.total_income for p in periods],
        "expenses": [p.total_expenses for p in periods],
        "savings": [p.savings for p in periods],
    }

    # --- Patterns ---
    patterns = _detect_patterns(periods)

    # --- Behavioural insights ---
    insights = []
    
    # Recurring vs Variable Income Analysis
    fixed_incomes = [p.fixed_income for p in periods if p.fixed_income > 0]
    var_entries = [(p.period_id, p.variable_income) for p in periods if p.variable_income > 0]
    if fixed_incomes:
        avg_fixed = sum(fixed_incomes) / len(fixed_incomes)
        if all(abs(f - avg_fixed) < 1.0 for f in fixed_incomes):
            if var_entries:
                var_str = ", ".join([f"₹{amt:,.0f} in {pid}" for pid, amt in var_entries])
                insights.append(
                    f"Your recurring income remained stable at ₹{avg_fixed:,.0f}/month. Variable income ({var_str}) provided temporary boosts."
                )
            else:
                insights.append(f"Your recurring income remained consistent at ₹{avg_fixed:,.0f}/month across all months.")

    if category_comparison:
        top = category_comparison[0]
        if top["diff"] > 0:
            insights.append(f"{top['category']} was ₹{top['diff']:,.0f} higher in the latest month compared to the earliest month in this range.")
        elif top["diff"] < 0:
            if top["last_month"] == 0:
                insights.append(f"No {top['category']} spending recorded in the latest month (was ₹{top['first_month']:,.0f} originally).")
            else:
                insights.append(f"{top['category']} was reduced by ₹{abs(top['diff']):,.0f} in the latest month compared to the earliest month in this range.")

    insights.extend(patterns)

    return {
        "has_data": True,
        "is_incomplete": curr.status == "incomplete",
        "current_period": curr.period_id,
        "previous_period": prev.period_id,
        "months_data": months_data,
        "avg_income": avg_income,
        "avg_expenses": avg_expenses,
        "avg_savings": avg_savings,
        "best_month": {"period": best_month.period_id, "savings": best_month.savings},
        "worst_month": {"period": worst_month.period_id, "savings": worst_month.savings},
        "latest_changes": {
            "income_change": (income_change * 100) if income_change is not None else 0.0,
            "expense_change": (expense_change * 100) if expense_change is not None else 0.0,
            "savings_change": (savings_change * 100) if savings_change is not None else 0.0,
        },
        "category_comparison": category_comparison,
        "chart_data": chart_data,
        "insights": insights,
    }


# ---------------------------------------------------------------------------
# YEARLY ANALYSIS
# ---------------------------------------------------------------------------

def build_yearly_analysis(periods: List[FinancialPeriod]) -> Dict[str, Any]:
    """
    Compares first half vs second half of the provided periods, with monthly
    trend data, category shifts, savings rate comparison, recurring vs variable income intelligence,
    and long-term insights. Designed for 12 months but works with any count >= 2.
    """
    if len(periods) < 2:
        return {"has_data": False}

    midpoint = len(periods) // 2
    first_half = periods[:midpoint]
    second_half = periods[midpoint:]

    def aggregate_half(half: List[FinancialPeriod]) -> Dict[str, Any]:
        income = sum(p.total_income for p in half)
        fixed_income = sum(p.fixed_income for p in half)
        variable_income = sum(p.variable_income for p in half)
        expenses = sum(p.total_expenses for p in half)
        savings = sum(p.savings for p in half)
        savings_rate = (savings / income) if income > 0 else 0.0
        cats: Dict[str, float] = {}
        for p in half:
            for c, amt in p.categories.items():
                cats[c] = cats.get(c, 0.0) + amt
        return {
            "income": income,
            "fixed_income": fixed_income,
            "variable_income": variable_income,
            "expenses": expenses,
            "savings": savings,
            "savings_rate": savings_rate,
            "categories": cats,
            "months": len(half),
        }

    h1_data = aggregate_half(first_half)
    h2_data = aggregate_half(second_half)

    is_incomplete = periods[-1].status == "incomplete"

    income_change = percentage_change(h2_data["income"], h1_data["income"]) if not is_incomplete else None
    fixed_change = percentage_change(h2_data["fixed_income"], h1_data["fixed_income"]) if not is_incomplete else None
    expense_change = percentage_change(h2_data["expenses"], h1_data["expenses"]) if not is_incomplete else None
    savings_change = percentage_change(h2_data["savings"], h1_data["savings"]) if not is_incomplete else None

    # --- Recurring vs Variable Income Intelligence ---
    import calendar
    var_first_half = []
    for p in first_half:
        if p.variable_income > 0:
            m_name = calendar.month_name[int(p.period_id.split("-")[1])] if "-" in p.period_id else p.period_id
            var_first_half.append((m_name, p.variable_income))

    monthly_fixed_h1 = h1_data["fixed_income"] / h1_data["months"] if h1_data["months"] > 0 else 0

    has_one_time_var = (
        h1_data["variable_income"] > 0 and
        h2_data["variable_income"] == 0 and
        (fixed_change is None or abs(fixed_change) < 0.02)
    )

    if has_one_time_var and income_change is not None:
        var_month_name = var_first_half[0][0] if var_first_half else "January"
        income_narrative = (
            f"your recurring salary held steady at ₹{monthly_fixed_h1:,.0f}/month "
            f"(with recorded income down {abs(income_change) * 100:.1f}% due to one-time variable freelance income in {var_month_name})"
        )
        context_income_insight = (
            f"Recorded income decreased by {abs(income_change) * 100:.1f}%, mainly because variable freelance income was present only in the first period. "
            f"Your recurring salary remained stable."
        )
        recurring_salary_insight = (
            f"Your recurring income remained stable at ₹{monthly_fixed_h1:,.0f}/month. "
            f"The income change was mainly due to a one-time freelance income of ₹{h1_data['variable_income']:,.0f} recorded in {var_month_name}."
        )
    elif fixed_change is not None and abs(fixed_change) >= 0.02:
        dir_fixed = "increased" if fixed_change > 0 else "decreased"
        income_narrative = f"your recurring income {dir_fixed} by {abs(fixed_change) * 100:.1f}%"
        context_income_insight = f"Recurring income {dir_fixed} by {abs(fixed_change) * 100:.1f}% between both periods."
        recurring_salary_insight = None
    else:
        income_narrative = f"your recurring income remained stable at ₹{monthly_fixed_h1:,.0f}/month"
        context_income_insight = f"Your recurring salary remained consistent at ₹{monthly_fixed_h1:,.0f}/month across both periods."
        recurring_salary_insight = None

    # --- Narrative ---
    def _change_str(val: Optional[float], metric_name: str, invert_color: bool = False) -> str:
        if val is None or val == 0:
            return f"{metric_name} remained flat"
        direction = "increased" if val > 0 else "decreased"
        return f"{metric_name} {direction} by {abs(val) * 100:.1f}%"

    narrative = (
        f"{income_narrative.capitalize()}, while "
        f"{_change_str(expense_change, 'expenses').lower()}, resulting in "
        f"{_change_str(savings_change, 'savings').lower()}."
    )

    # --- Category shifts ---
    all_cats = set(h1_data["categories"].keys()).union(h2_data["categories"].keys())
    category_changes = []
    for cat in all_cats:
        c1 = h1_data["categories"].get(cat, 0.0)
        c2 = h2_data["categories"].get(cat, 0.0)
        diff = c2 - c1
        if abs(diff) >= 1:
            category_changes.append({
                "category": cat,
                "h1": c1,
                "h2": c2,
                "diff": diff,
                "change_pct": percentage_change(c2, c1),
                "is_zero_spending": (c2 == 0.0 and c1 > 0.0)
            })
    category_changes.sort(key=lambda x: abs(x["diff"]), reverse=True)

    # --- Monthly trend chart data ---
    chart_data = {
        "labels": [p.period_id for p in periods],
        "income": [p.total_income for p in periods],
        "expenses": [p.total_expenses for p in periods],
        "savings": [p.savings for p in periods],
    }

    # --- Long-term insights ---
    long_term_insights = []

    # 1. Income Context & Recurring Insights
    if recurring_salary_insight:
        long_term_insights.append(recurring_salary_insight)
    if context_income_insight:
        long_term_insights.append(context_income_insight)

    # 2. Savings rate comparison
    sr_diff = h2_data["savings_rate"] - h1_data["savings_rate"]
    if abs(sr_diff) >= 0.01:
        direction = "improved" if sr_diff > 0 else "declined"
        long_term_insights.append(
            f"Your savings rate {direction} from {h1_data['savings_rate'] * 100:.1f}% to {h2_data['savings_rate'] * 100:.1f}%."
        )

    # 3. Top category contributors to savings change
    if category_changes:
        top_increase = [c for c in category_changes if c["diff"] > 0]
        top_decrease = [c for c in category_changes if c["diff"] < 0]
        if top_increase:
            c = top_increase[0]
            long_term_insights.append(
                f"{c['category']} spending grew by ₹{c['diff']:,.0f} between the two halves, putting pressure on savings."
            )
        if top_decrease:
            c = top_decrease[0]
            if c["h2"] == 0:
                long_term_insights.append(
                    f"No {c['category']} spending was recorded in the second half (reduced by ₹{abs(c['diff']):,.0f} compared to the first half)."
                )
            else:
                long_term_insights.append(
                    f"{c['category']} spending reduced by ₹{abs(c['diff']):,.0f} between the two halves, contributing to savings."
                )

    return {
        "has_data": True,
        "is_incomplete": is_incomplete,
        "h1_label": f"{first_half[0].period_id} to {first_half[-1].period_id}",
        "h2_label": f"{second_half[0].period_id} to {second_half[-1].period_id}",
        "h1_data": h1_data,
        "h2_data": h2_data,
        "income_change": income_change,
        "expense_change": expense_change,
        "savings_change": savings_change,
        "narrative": narrative,
        "category_changes": category_changes,
        "chart_data": chart_data,
        "long_term_insights": long_term_insights,
    }
