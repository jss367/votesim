from typing import Dict, List, Set, Tuple

from votesim.helpers import CandidateResult, CandidateStatus, ElectionResults, RoundResult
from votesim.models import Candidate


class SmithApprovalBallot:
    """A ballot for Smith-Approval voting that contains both ranked preferences and approval choices."""

    def __init__(self, ranked_candidates: List[Candidate], approved_candidates: List[Candidate]):
        self.ranked_candidates = tuple(ranked_candidates)
        self.approved_candidates = tuple(approved_candidates)

        if len(set(ranked_candidates)) != len(ranked_candidates):
            raise ValueError("Duplicate candidates in ranked list")
        if len(set(approved_candidates)) != len(approved_candidates):
            raise ValueError("Duplicate candidates in approval list")

        approved_set = set(approved_candidates)
        ranked_set = set(ranked_candidates)
        if not approved_set.issubset(ranked_set):
            raise ValueError("All approved candidates must also be ranked")

    def __repr__(self) -> str:
        ranked = ", ".join(str(c) for c in self.ranked_candidates)
        approved = ", ".join(str(c) for c in self.approved_candidates)
        return f"Smith-Approval ballot: [Ranked: {ranked}] [Approved: {approved}]"


def get_pairwise_victories(
    candidates: List[Candidate], ballots: List[SmithApprovalBallot]
) -> Dict[Tuple[Candidate, Candidate], int]:
    """Compute pairwise victories between all candidates."""
    victories = {}

    for i, cand1 in enumerate(candidates):
        for cand2 in candidates[i + 1 :]:
            prefer_1 = 0
            prefer_2 = 0

            for ballot in ballots:
                for candidate in ballot.ranked_candidates:
                    if candidate == cand1:
                        prefer_1 += 1
                        break
                    elif candidate == cand2:
                        prefer_2 += 1
                        break

            if prefer_1 >= prefer_2:
                victories[(cand1, cand2)] = prefer_1 - prefer_2
            if prefer_2 >= prefer_1:
                victories[(cand2, cand1)] = prefer_2 - prefer_1

    return victories


def beats(cand1: Candidate, cand2: Candidate, victories: Dict[Tuple[Candidate, Candidate], int]) -> bool:
    """Check if candidate 1 strictly beats candidate 2."""
    return (cand1, cand2) in victories and (
        (cand2, cand1) not in victories or victories[(cand1, cand2)] > victories[(cand2, cand1)]
    )


def get_smith_set(candidates: List[Candidate], victories: Dict[Tuple[Candidate, Candidate], int]) -> Set[Candidate]:
    """Find the Smith set - smallest set of candidates that beats all others pairwise."""

    def dominates(cand1: Candidate, cand2: Candidate) -> bool:
        return beats(cand1, cand2, victories)

    current_set = set(candidates)

    while True:
        can_remove = set()

        for cand in current_set:
            for other in current_set:
                if other != cand and dominates(other, cand):
                    dominated_by_cand = {c for c in current_set if dominates(cand, c)}
                    dominates_cand = {c for c in current_set if dominates(c, cand)}
                    if not (dominated_by_cand - dominates_cand):
                        can_remove.add(cand)
                        break

        if not can_remove:
            break

        weakest = min(can_remove, key=lambda c: sum(1 for x in current_set if dominates(c, x)))
        current_set.remove(weakest)

    return current_set


def get_approval_scores(candidates: List[Candidate], ballots: List[SmithApprovalBallot]) -> Dict[Candidate, int]:
    """Count approval votes for each candidate."""
    scores = {candidate: 0 for candidate in candidates}
    for ballot in ballots:
        for candidate in ballot.approved_candidates:
            scores[candidate] += 1
    return scores


def smith_approval(candidates: List[Candidate], ballots: List[SmithApprovalBallot]) -> ElectionResults:
    """
    Run a Smith-Approval election.

    Args:
        candidates: List of all candidates
        ballots: List of SmithApprovalBallot objects containing both ranked and approval choices

    Returns:
        ElectionResults object with winner(s)
    """
    print("\nComputing pairwise victories...")
    victories = get_pairwise_victories(candidates, ballots)
    # Print pairwise victories
    for (cand1, cand2), margin in victories.items():
        print(f"{cand1} beats {cand2} by {margin} votes")

    print("\nFinding Smith set...")
    smith_set = get_smith_set(candidates, victories)
    print("Smith set:", ", ".join(str(c) for c in smith_set))

    print("\nCounting approval votes...")
    approval_scores = get_approval_scores(candidates, ballots)
    # Print approval scores for Smith set members
    print("Approval scores for Smith set:")
    for candidate in smith_set:
        print(f"{candidate}: {approval_scores[candidate]} approvals")

    # Find winner from Smith set with highest approval
    winner = max(smith_set, key=lambda c: approval_scores[c])
    print(f"\nWinner from Smith set (highest approval): {winner}")

    # Create election results
    results = ElectionResults()

    # Create candidate results
    candidate_results = []
    for candidate in candidates:
        status = CandidateStatus.Elected if candidate == winner else CandidateStatus.Rejected
        in_smith = "In Smith set" if candidate in smith_set else "Not in Smith set"
        result = CandidateResult(
            candidate=f"{candidate} ({in_smith})", number_of_votes=approval_scores[candidate], status=status
        )
        candidate_results.append(result)

    # Sort by approval votes
    candidate_results.sort(key=lambda x: x.number_of_votes, reverse=True)

    # Create and register round result
    round_result = RoundResult(candidate_results=candidate_results, number_of_blank_votes=0)
    results.register_round_results(round_result)

    return results
