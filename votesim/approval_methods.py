from typing import List
from votesim.models import Candidate


class ApprovalBallot:
    def __init__(self, candidates: List) -> None:
        self.candidates: List[Candidate] = candidates

    def __repr__(self) -> str:
        candidate_name = ", ".join([candidate.name for candidate in self.candidates])
        return f"Approval ballot: {candidate_name}"


class ApprovalElection:
    """
    Starting with approval election
    """

    def __init__(self, candidates):
        self.candidates = candidates

    def calc_results(self, ballots):
        self.results = {candidate: 0 for candidate in self.candidates}
        for ballot in ballots:
            for candidate in ballot.candidates:
                self.results[candidate] += 1
        # print(self.results)

    def run_election(self, ballots):
        self.calc_results(ballots)
        self.display_results(self.results)

    @staticmethod
    def display_results(results: dict):
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        for res in sorted_results:
            print(f"Candidate: {res[0]} -- Votes: {res[1]}")

    @staticmethod
    def find_winner(results: dict):
        #         winners = max(results.items(), key=lambda x: x[1])
        winners = [k for (k, v) in results.items() if v == max(results.values())]
        if len(winners) == 1:
            print(f"Winner: {winners[0]}")
        else:
            print(f"Multiple Winners: {winners}")
