import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from planning.insights import generate_planning_insight
from recommendations.engine import generate_recommendations

class TestStabilization(unittest.TestCase):
    def test_planning_emi_below_savings(self):
        insight = generate_planning_insight(5000, 10000, "EMI")
        self.assertEqual(insight["status"], "SUCCESS")
        
    def test_planning_emi_exceeds_savings(self):
        insight = generate_planning_insight(15000, 10000, "EMI")
        self.assertEqual(insight["status"], "WARNING")
        
    def test_planning_sip_exceeds_savings(self):
        insight = generate_planning_insight(15000, 10000, "SIP")
        self.assertEqual(insight["status"], "WARNING")
        
    def test_planning_empty_savings(self):
        insight = generate_planning_insight(5000, 0, "SIP")
        self.assertEqual(insight["status"], "WARNING")
        
    def test_recommendation_empty(self):
        recs = generate_recommendations([], [], {}, {})
        self.assertIsInstance(recs, list)

if __name__ == "__main__":
    unittest.main()
