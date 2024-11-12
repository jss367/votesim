from typing import Dict, List, Set, Tuple

from votesim.approval_methods import ApprovalBallot
from votesim.helpers import CandidateResult, CandidateStatus, ElectionResults, RoundResult
from votesim.models import Ballot, Candidate


def get_pairwise_victories(
    candidates: List[Candidate], ballots: List[Ballot]
) -> Dict[Tuple[Candidate, Candidate], int]:
    """
    Compute pairwise victories between all candidates.
    Returns a dictionary mapping (winner, loser) pairs to victory margin.
    """
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


def beats_or_ties(cand1: Candidate, cand2: Candidate, victories: Dict[Tuple[Candidate, Candidate], int]) -> bool:
    """Helper function to check if candidate 1 beats or ties candidate 2."""
    # If cand1 beats cand2 with a positive margin, or neither beats the other (tie)
    return (
        ((cand1, cand2) in victories and (cand2, cand1) not in victories)
        or ((cand1, cand2) in victories and (cand2, cand1) in victories)
        or ((cand1, cand2) not in victories and (cand2, cand1) not in victories)
    )


def get_smith_set(candidates: List[Candidate], victories: Dict[Tuple[Candidate, Candidate], int]) -> Set[Candidate]:
    """
    Find the Smith set - smallest set of candidates that beats all others pairwise.
    A candidate is in the Smith set if they beat or tie all candidates outside the set.
    """
    # Start with all candidates
    smith_set = set(candidates)

    # Keep removing candidates until we can't anymore
    changed = True
    while changed:
        changed = False
        for cand in list(smith_set):  # Create list to avoid modifying set during iteration
            # Check if this candidate should be in Smith set
            # They must beat or tie ALL candidates outside current Smith set
            beats_or_ties_all_outside = True
            for other in candidates:
                if other == cand or other in smith_set:
                    continue

                # If they don't beat or tie this outside candidate, they shouldn't be in Smith set
                if not beats_or_ties(cand, other, victories):
                    beats_or_ties_all_outside = False
                    break

            # If they don't beat or tie all outside candidates, remove them
            if not beats_or_ties_all_outside:
                smith_set.remove(cand)
                changed = True

    # Handle special case: if smith_set is empty, return candidate(s) with most pairwise victories
    if not smith_set:
        win_counts = {c: 0 for c in candidates}
        for winner, _ in victories:
            win_counts[winner] += 1
        max_wins = max(win_counts.values())
        smith_set = {c for c in candidates if win_counts[c] == max_wins}

    return smith_set


def get_approval_scores(candidates: List[Candidate], approval_ballots: List[ApprovalBallot]) -> Dict[Candidate, int]:
    """
    Count approval votes for each candidate.
    """
    scores = {candidate: 0 for candidate in candidates}
    for ballot in approval_ballots:
        for candidate in ballot.candidates:
            scores[candidate] += 1
    return scores


def smith_approval(
    candidates: List[Candidate], ranked_ballots: List[Ballot], approval_ballots: List[ApprovalBallot]
) -> ElectionResults:
    """
    Implementation of Smith-Approval method:
    1. Use ranked ballots to find Smith set
    2. Among Smith set, select candidate with most approval votes

    Args:
        candidates: List of candidates
        ranked_ballots: List of ranked choice ballots
        approval_ballots: List of approval vote ballots

    Returns:
        ElectionResults object with winner
    """
    # Get pairwise victory information
    victories = get_pairwise_victories(candidates, ranked_ballots)

    # Find Smith set
    smith_set = get_smith_set(candidates, victories)

    # Get approval scores for Smith set candidates
    approval_scores = get_approval_scores(candidates, approval_ballots)

    # Find winner from Smith set with highest approval
    winner = max(smith_set, key=lambda c: approval_scores[c])

    # Create election results
    results = ElectionResults()

    # Create candidate results
    candidate_results = []
    for candidate in candidates:
        status = CandidateStatus.Elected if candidate == winner else CandidateStatus.Rejected
        result = CandidateResult(candidate=candidate, number_of_votes=approval_scores[candidate], status=status)
        candidate_results.append(result)

    # Sort by approval votes
    candidate_results.sort(key=lambda x: x.number_of_votes, reverse=True)

    # Create and register round result
    round_result = RoundResult(candidate_results=candidate_results, number_of_blank_votes=0)
    results.register_round_results(round_result)

    return results
