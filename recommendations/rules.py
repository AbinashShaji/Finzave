# Static deterministic mappings for recommendation engine
# Must not contain AI logic, new assumptions, or undefined frameworks.

RECOMMENDATION_MAPPINGS = {
    "RB-01": {
        "source": "RB-01",
        "category": "EXPENSES",
        "priority": "HIGH",
        "title": "Halt Expense Inflation",
        "message": "Your expenses have consistently increased over the last 3 periods. Review your recent transactions to identify and reduce non-essential spending."
    },
    "RB-02": {
        "source": "RB-02",
        "category": "EXPENSES",
        "priority": "MEDIUM",
        "title": "Unusual Spending Concentration",
        "message": "You have a category consuming an unusually high portion of your expenses compared to your historical average. Review this category for potential savings."
    },
    "RB-03": {
        "source": "RB-03",
        "category": "SAVINGS",
        "priority": "HIGH",
        "title": "Increase Savings Rate",
        "message": "Your savings rate is below the FinZave analysis threshold. Review your income and expense patterns to improve your savings position."
    },
    "RB-04": {
        "source": "RB-04",
        "category": "SAVINGS",
        "priority": "HIGH",
        "title": "Stabilize Declining Savings",
        "message": "Your savings have been declining over recent periods. Consider pausing large discretionary purchases until your surplus stabilizes."
    },
    "RB-05": {
        "source": "RB-05",
        "category": "INCOME_EXPENSE",
        "priority": "MEDIUM",
        "title": "Balance Growth",
        "message": "Your expenses are growing faster than your income. Adjust your budget to ensure spending does not outpace your earning capacity."
    },
    "RB-06": {
        "source": "RB-06",
        "category": "EXPENSES",
        "priority": "MEDIUM",
        "title": "Reduce Discretionary Spending",
        "message": "A significant portion of your expenses is going toward discretionary categories. Consider shifting funds from these areas toward your savings goals."
    },
    "RB-07": {
        "source": "RB-07",
        "category": "EXPENSES",
        "priority": "LOW",
        "title": "Monitor Category Spikes",
        "message": "Your spending in a specific category is unusually high compared to your historical average. Verify these are expected or one-off expenses."
    },
    "RB-08": {
        "source": "RB-08",
        "category": "SAVINGS",
        "priority": "LOW",
        "title": "Consistent Saver",
        "message": "Your savings pattern is currently positive based on the FinZave analysis threshold. Maintain this healthy habit."
    }
}
