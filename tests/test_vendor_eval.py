import sqlite3
import unittest
from vendor_eval import CRITERIA, add_pilot, connect, report, score

class VendorTests(unittest.TestCase):
    def test_weighted_score(self):
        self.assertEqual(score(dict.fromkeys(CRITERIA, 5)), 5)
    def test_bad_scores(self):
        with self.assertRaises(ValueError):
            score(dict.fromkeys(CRITERIA, 6))
    def test_persistence_and_ranking(self):
        with connect(':memory:') as conn:
            add_pilot(conn, 'A', dict.fromkeys(CRITERIA, 5))
            add_pilot(conn, 'B', dict.fromkeys(CRITERIA, 2))
            add_pilot(conn, 'A', dict.fromkeys(CRITERIA, 3))
            rows = report(conn)
            self.assertEqual(rows[0]['vendor'], 'A')
            self.assertEqual(rows[0]['runs'], 2)
            self.assertEqual(rows[0]['weighted_score'], 4)

if __name__ == '__main__': unittest.main()
