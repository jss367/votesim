import unittest

from votesim.models import Candidate
from votesim.smith_approval import (
    SmithApprovalBallot,
    get_approval_scores,
    get_pairwise_victories,
    get_smith_set,
    smith_approval,
)


class TestSmithApproval(unittest.TestCase):
    def setUp(self):
        self.a = Candidate("A")
        self.b = Candidate("B")
        self.c = Candidate("C")
        self.candidates = [self.a, self.b, self.c]

    def test_smith_approval_ballot(self):
        # Test valid ballot
        ballot = SmithApprovalBallot(ranked_candidates=[self.a, self.b, self.c], approved_candidates=[self.a, self.b])
        self.assertEqual(ballot.ranked_candidates, (self.a, self.b, self.c))
        self.assertEqual(ballot.approved_candidates, (self.a, self.b))

        # Test duplicate ranked candidates
        with self.assertRaises(ValueError):
            SmithApprovalBallot(ranked_candidates=[self.a, self.b, self.b], approved_candidates=[self.a])

        # Test duplicate approved candidates
        with self.assertRaises(ValueError):
            SmithApprovalBallot(ranked_candidates=[self.a, self.b, self.c], approved_candidates=[self.a, self.a])

        # Test approved not in ranked
        with self.assertRaises(ValueError):
            SmithApprovalBallot(ranked_candidates=[self.a, self.b], approved_candidates=[self.a, self.c])

    def test_pairwise_victories(self):
        ballots = [
            SmithApprovalBallot(ranked_candidates=[self.a, self.b, self.c], approved_candidates=[self.a]),
            SmithApprovalBallot(ranked_candidates=[self.b, self.c, self.a], approved_candidates=[self.b]),
            SmithApprovalBallot(ranked_candidates=[self.c, self.a, self.b], approved_candidates=[self.c]),
        ]

        victories = get_pairwise_victories(self.candidates, ballots)

        self.assertEqual(victories[(self.a, self.b)], 1)
        self.assertEqual(victories[(self.b, self.c)], 1)
        self.assertEqual(victories[(self.c, self.a)], 1)

    def test_smith_set(self):
        # Test case where B beats A, C beats B, but A beats C (cycle)
        victories = {(self.b, self.a): 1, (self.c, self.b): 1, (self.a, self.c): 1}

        smith = get_smith_set(self.candidates, victories)
        self.assertEqual(smith, set(self.candidates))

        # Test case with clear winner
        victories = {(self.a, self.b): 1, (self.a, self.c): 1, (self.b, self.c): 1}

        smith = get_smith_set(self.candidates, victories)
        self.assertEqual(smith, {self.a})

    def test_approval_scores(self):
        ballots = [
            SmithApprovalBallot(ranked_candidates=[self.a, self.b, self.c], approved_candidates=[self.a, self.b]),
            SmithApprovalBallot(ranked_candidates=[self.b, self.c, self.a], approved_candidates=[self.b, self.c]),
            SmithApprovalBallot(ranked_candidates=[self.c, self.a, self.b], approved_candidates=[self.a, self.c]),
        ]

        scores = get_approval_scores(self.candidates, ballots)

        self.assertEqual(scores[self.a], 2)
        self.assertEqual(scores[self.b], 2)
        self.assertEqual(scores[self.c], 2)

    def test_smith_approval_integration(self):
        # Test with SmithApprovalBallots
        ballots = [
            SmithApprovalBallot(ranked_candidates=[self.a, self.b, self.c], approved_candidates=[self.a, self.b]),
            SmithApprovalBallot(ranked_candidates=[self.b, self.c, self.a], approved_candidates=[self.b, self.c]),
            SmithApprovalBallot(ranked_candidates=[self.c, self.a, self.b], approved_candidates=[self.b]),
        ]

        result = smith_approval(self.candidates, ballots)
        winners = result.get_winners()
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0], self.b)  # B should win with most approval votes


if __name__ == '__main__':
    unittest.main()
