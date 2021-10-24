"""
Models that are used by multiple_seat_ranking_methods.py

You can create and use your own Candidate and Ballot models as long as they implement the same properties and methods.
"""
from typing import List


class Candidate:
    """A candidate in the election."""

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if other is None:
            return False

        return self.name == other.name


class DuplicateCandidatesError(RuntimeError):
    pass


class ApprovalBallot:
    def __init__(self, candidates: List) -> None:
        self.candidates: List[Candidate] = tuple


class Ballot:
    """
    A ballot (vote) where the voter has ranked all, or just some, of the candidates.

    If a voter lists one candidate multiple times, a DuplicateCandidatesError is thrown.
    """

    def __init__(self, ranked_candidates: List[Candidate]):
        """
        TODO: Why does this need to be a tuple?
        """
        self.ranked_candidates: List[Candidate] = tuple(ranked_candidates)

        if Ballot._is_duplicates(ranked_candidates):
            raise DuplicateCandidatesError

        if not Ballot._is_all_candidate_objects(ranked_candidates):
            raise TypeError(
                "Not all objects in ranked candidate list are of class Candidate or "
                "implement the same properties and methods"
            )

    def __repr__(self) -> str:
        candidate_name = ", ".join([candidate.name for candidate in self.ranked_candidates])
        return f"Ranked ballot: {candidate_name}"

    @staticmethod
    def _is_duplicates(ranked_candidates) -> bool:
        return len(set(ranked_candidates)) is not len(ranked_candidates)

    @staticmethod
    def _is_all_candidate_objects(objects) -> bool:
        return all(Ballot._is_candidate_object(obj) for obj in objects)

    @staticmethod
    def _is_candidate_object(obj) -> bool:
        if obj.__class__ is Candidate:
            return True

        is_candidate_like = all([hasattr(obj, "name"), hasattr(obj, "__hash__"), hasattr(obj, "__eq__")])

        return is_candidate_like
