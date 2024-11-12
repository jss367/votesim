import unittest

from votesim.approval_methods import ApprovalBallot
from votesim.models import Ballot, Candidate
from votesim.smith_approval import get_approval_scores, get_pairwise_victories, get_smith_set, smith_approval


class TestSmithApproval(unittest.TestCase):
    def setUp(self):
        # Create some test candidates
        self.a = Candidate("A")
        self.b = Candidate("B")
        self.c = Candidate("C")
        self.candidates = [self.a, self.b, self.c]

    def test_pairwise_victories(self):
        # Create ranked ballots with a cycle: A>B>C>A
        ballots = [
            Ballot(ranked_candidates=[self.a, self.b, self.c]),  # 2 voters prefer A>B>C
            Ballot(ranked_candidates=[self.a, self.b, self.c]),
            Ballot(ranked_candidates=[self.b, self.c, self.a]),  # 2 voters prefer B>C>A
            Ballot(ranked_candidates=[self.b, self.c, self.a]),
            Ballot(ranked_candidates=[self.c, self.a, self.b]),  # 2 voters prefer C>A>B
            Ballot(ranked_candidates=[self.c, self.a, self.b]),
        ]

        victories = get_pairwise_victories(self.candidates, ballots)

        # With this setup, each candidate should beat one other by 2 votes
        self.assertEqual(victories[(self.a, self.b)], 2)
        self.assertEqual(victories[(self.b, self.c)], 2)
        self.assertEqual(victories[(self.c, self.a)], 2)

    def test_smith_set(self):
        # Test case where B beats A, C beats B, but A beats C (cycle)
        victories = {(self.b, self.a): 1, (self.c, self.b): 1, (self.a, self.c): 1}

        smith = get_smith_set(self.candidates, victories)

        # All candidates should be in Smith set due to cycle
        self.assertEqual(smith, set(self.candidates))

        # Test case with clear winner
        victories = {(self.a, self.b): 1, (self.a, self.c): 1, (self.b, self.c): 1}

        smith = get_smith_set(self.candidates, victories)

        # Only A should be in Smith set
        self.assertEqual(smith, {self.a})

    def test_approval_scores(self):
        approval_ballots = [
            ApprovalBallot([self.a, self.b]),
            ApprovalBallot([self.b, self.c]),
            ApprovalBallot([self.a, self.c]),
        ]

        scores = get_approval_scores(self.candidates, approval_ballots)

        self.assertEqual(scores[self.a], 2)
        self.assertEqual(scores[self.b], 2)
        self.assertEqual(scores[self.c], 2)

    def test_smith_approval_integration(self):
        # Create a scenario where:
        # - All candidates are in Smith set (cycle in rankings)
        # - B has most approval votes
        ranked_ballots = [
            Ballot(ranked_candidates=[self.a, self.b, self.c]),
            Ballot(ranked_candidates=[self.b, self.c, self.a]),
            Ballot(ranked_candidates=[self.c, self.a, self.b]),
        ]

        approval_ballots = [
            ApprovalBallot([self.a, self.b]),
            ApprovalBallot([self.b, self.c]),
            ApprovalBallot([self.b]),  # Extra approval for B
        ]

        result = smith_approval(self.candidates, ranked_ballots, approval_ballots)

        # B should win since it has most approval votes among Smith set
        winners = result.get_winners()
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0], self.b)


if __name__ == '__main__':
    unittest.main()
