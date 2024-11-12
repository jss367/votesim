"""
Analyzes the Burlington 2009 mayoral election data using Instant Runoff Voting.
File format expects data in the format:
    number_of_ballots: candidate_code>candidate_code>...
Example:
    123: K>W>M
"""

import re
from typing import Dict, List

from votesim import Ballot, Candidate, instant_runoff_voting

# Define election candidates
CANDIDATES = {
    "K": Candidate("Bob Kiss"),
    "W": Candidate("Kurt Wright"),
    "M": Candidate("Andy Montroll"),
    "H": Candidate("Dan Smith"),
    "N": Candidate("James Simpson"),
    "R": Candidate("Write-in"),
}


def parse_ballot_line(line: str, candidate_map: Dict[str, Candidate]) -> tuple[int, List[Candidate]]:
    """
    Parse a single line of ballot data.

    Args:
        line: String containing ballot count and rankings (e.g. "123: K>W>M")
        candidate_map: Mapping of candidate codes to Candidate objects

    Returns:
        Tuple of (number of ballots, list of ranked candidates)

    Raises:
        ValueError: If line format is invalid or contains unknown candidates
    """
    match = re.search(r"(\d+): ((\w>?)+)", line)
    if not match:
        raise ValueError(f"Invalid ballot line format: {line}")

    num_ballots = int(match.group(1))
    ranked_codes = match.group(2).split(">")

    try:
        ranked_candidates = [candidate_map[code] for code in ranked_codes]
    except KeyError as e:
        raise ValueError(f"Unknown candidate code: {e.args[0]}")

    return num_ballots, ranked_candidates


def main():
    # Read and parse ballot data
    ballots: List[Ballot] = []
    filename = "test_data/JLburl09.txt"

    try:
        with open(filename, "r") as f:
            # Skip header lines and read ballot data (lines 18-395)
            lines = f.readlines()[18:395]

            for line in lines:
                try:
                    num_ballots, ranked_candidates = parse_ballot_line(line, CANDIDATES)
                    ballot = Ballot(ranked_candidates)
                    ballots.extend([ballot] * num_ballots)
                except ValueError as e:
                    print(f"Error parsing ballot: {e}")
                    continue

    except FileNotFoundError:
        print(f"Election data file not found: {filename}")
        return

    # Run election analysis
    election_result = instant_runoff_voting(list(CANDIDATES.values()), ballots)
    winners = election_result.get_winners()

    # Print results
    print("\n=== Burlington 2009 Mayoral Election Results ===")
    print(election_result)
    print("\nWinner(s):", [winner.name for winner in winners])


if __name__ == "__main__":
    main()
