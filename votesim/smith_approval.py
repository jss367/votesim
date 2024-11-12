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


def get_smith_set(candidates: List[Candidate], victories: Dict[Tuple[Candidate, Candidate], int]) -> Set[Candidate]:
    """
    Find the Smith set - smallest set of candidates that beats all others pairwise.
    """
    smith_set = set(candidates)
    changed = True

    while changed:
        changed = False
        for cand in candidates:
            if cand not in smith_set:
                continue

            # Check if this candidate loses to any candidate outside smith set
            loses_to_non_smith = False
            for other in candidates:
                if other == cand or other in smith_set:
                    continue

                # Check if other candidate beats current candidate
                if (other, cand) in victories and (cand, other) not in victories:
                    loses_to_non_smith = True
                    break

            if loses_to_non_smith:
                smith_set.remove(cand)
                changed = True

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
