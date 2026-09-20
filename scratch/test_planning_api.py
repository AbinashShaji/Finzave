import os
import sys
import unittest
from flask import Flask
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planning.sip import calculate_sip
from planning.emi import calculate_emi
from planning.insights import generate_planning_insight

class TestPlanningAPI(unittest.TestCase):
    
    def test_sip_calculation(self):
        result = calculate_sip(10000, 12, 10)
        self.assertIn("future_value", result)
        self.assertIn("total_invested", result)
        self.assertIn("est_returns", result)
        self.assertTrue(result["future_value"] > 0)
        
    def test_emi_calculation(self):
        result = calculate_emi(5000000, 8.5, 20)
        self.assertIn("monthly_emi", result)
        self.assertIn("total_interest", result)
        self.assertIn("total_payment", result)
        self.assertTrue(result["monthly_emi"] > 0)
        
    def test_insight_payload_unchanged(self):
        insight = generate_planning_insight(15000, 10000, "EMI")
        self.assertEqual(insight["status"], "WARNING")
        self.assertIn("message", insight)

if __name__ == "__main__":
    unittest.main()
