"""Tests for external IRV election cases"""

import os
from dataclasses import dataclass
from typing import Any, List, Optional

import pandas as pd
import pytest

from votesim.models import Ballot, Candidate
from votesim.single_seat_ranking_methods import instant_runoff_voting
from votesim.test_helpers import assert_list_almost_equal


@dataclass
class TestCase:
    def assertEqual(self, a: Any, b: Any, msg: Optional[str] = None) -> None:
        """Assert that two values are equal"""
        assert a == b, msg or f"{a} != {b}"

    def assertTrue(self, expr: bool, msg: Optional[str] = None) -> None:
        """Assert that expression is True"""
        assert expr, msg or "Expression is not True"

    def assert_list_almost_equal(self, *args, **kwargs):
        """Helper method to match interface"""
        assert_list_almost_equal(self, *args, **kwargs)


def analyze_ballot_patterns(df: pd.DataFrame) -> None:
    """Analyze patterns in the ballot data"""
    print("\nBallot Pattern Analysis:")
    patterns = {}
    # max_rank = df['rank'].max()

    # Count patterns by ballot
    for ballot_id, group in df.groupby('ballot_id'):
        choices = []
        ranks = group.sort_values('rank')['rank'].tolist()
        ranked_choices = group.sort_values('rank')['choice'].tolist()

        # Check for gaps in ranks
        has_gaps = ranks != list(range(1, len(ranks) + 1))

        # Convert to pattern
        for choice in ranked_choices:
            if choice.startswith('$'):
                choices.append(choice[1:])  # Remove $ prefix
            else:
                choices.append('VOTE')
        pattern = tuple(choices)
        patterns[pattern] = patterns.get(pattern, 0) + 1
        if has_gaps:
            print(f"Ballot {ballot_id} has rank gaps: {ranks}, choices: {ranked_choices}")

    # Print patterns sorted by frequency
    print("\nMost common ballot patterns:")
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {pattern}: {count} ballots")


def process_election_file(file_name: str) -> tuple[List[Ballot], List[Candidate], pd.DataFrame, int]:
    """Process election data file and return ballots and candidates"""
    data_dir = "tests/test_data/external_irv"
    file_path = os.path.join(data_dir, file_name)

    # Read the CSV file
    df = pd.read_csv(file_path)

    # Print diagnostic information
    special_values = df[df['choice'].str.startswith('$')]['choice'].unique()
    print("\nSpecial values found in data:")
    for val in special_values:
        count = len(df[df['choice'] == val])
        ballot_count = len(df[df['choice'] == val]['ballot_id'].unique())
        print(f"  {val}: {count} occurrences in {ballot_count} ballots")

    # Analyze ballot patterns
    analyze_ballot_patterns(df)

    # Get unique candidates (excluding special values)
    unique_candidates = sorted(df[~df['choice'].str.startswith('$')]['choice'].unique())
    candidates = [Candidate(name) for name in unique_candidates]
    candidate_map = {name: candidate for name, candidate in zip(unique_candidates, candidates)}

    # Process ballots and count invalid votes
    ballots = []
    invalid_count = 0

    # First pass: look for patterns that invalidate entire ballots
    for ballot_id, group in df.groupby('ballot_id'):
        group_sorted = group.sort_values('rank')
        ranks = group_sorted['rank'].tolist()
        choices = group_sorted['choice'].tolist()

        # Check if ballot has gaps in ranks
        if ranks != list(range(1, len(ranks) + 1)):
            invalid_count += 1
            continue

        # Check for overvotes
        if any(c == '$OVERVOTE' for c in choices):
            invalid_count += 1
            continue

        # Check for blank ballot
        if all(c == '$UNDERVOTE' for c in choices):
            invalid_count += 1
            continue

        # Process ballot
        ranked_candidates = []
        for choice in choices:
            if choice == '$UNDERVOTE':
                break
            if choice in candidate_map and candidate_map[choice] not in ranked_candidates:
                ranked_candidates.append(candidate_map[choice])

        if ranked_candidates:
            ballots.append(Ballot(ranked_candidates))
        else:
            invalid_count += 1

    return ballots, candidates, df, invalid_count


def run_election_test(file_name: str, expected_blank_votes: int, expected_votes: List[int]) -> None:
    """Run election test with given file and expected results"""
    test_case = TestCase()

    # Process election data
    print(f"\nProcessing {file_name}")
    ballots, candidates, df, blank_votes = process_election_file(file_name)

    # Run election
    election_result = instant_runoff_voting(candidates, ballots)
    final_round = election_result.rounds[-1]
    actual_votes = [result.number_of_votes for result in final_round.candidate_results]

    # Print and verify results
    print(f"\nElection Results for {file_name}:")
    print("Final round candidates and votes:")
    for result in final_round.candidate_results:
        print(f"  {result.candidate.name}: {result.number_of_votes:.1f}")
    print("\nBallot counts:")
    print(f"Total unique ballots: {df['ballot_id'].nunique()}")
    print(f"Valid ballots: {len(ballots)}")
    print(f"Invalid/blank ballots: {blank_votes}")
    print(f"Expected blank votes: {expected_blank_votes}")
    print("Actual vs Expected:")
    print(f"  Blank votes: {blank_votes} vs {expected_blank_votes}")
    print(f"  Vote totals: {[round(v, 1) for v in actual_votes]} vs {expected_votes}")

    # Assert results match expectations
    test_case.assert_list_almost_equal([expected_blank_votes], [blank_votes])
    test_case.assert_list_almost_equal(expected_votes, actual_votes)


@pytest.mark.skip(reason="External IRV tests need fixing")
def test_burlington_2009_mayor():
    """
    Burlington 2009 Mayoral Election
    Source: https://ranked.vote/us/vt/btv/2009/03/mayor/
    Data source: https://s3.amazonaws.com/ranked.vote-reports/us/vt/btv/2009/03/mayor/us_vt_btv_2009_03_mayor.normalized.csv.gz
    """
    run_election_test(
        file_name='us_vt_btv_2009_03_mayor.normalized.csv',
        expected_blank_votes=607,
        expected_votes=[4313, 4060, 0, 0, 0, 0],
    )


@pytest.mark.skip(reason="External IRV tests need fixing")
def test_maine_2018_cd2_primary():
    """
    Test Maine 2018 Congress District 2 Democrat Primary Election
    Source: https://ranked.vote/us/me/2018/06/cd02-primary/
    Data source: https://s3.amazonaws.com/ranked.vote-reports/us/me/2018/06/cd02-primary/us_me_2018_06_cd02-primary.normalized.csv.gz
    """
    run_election_test(
        file_name='us_me_2018_06_cd02-primary.normalized.csv',
        expected_blank_votes=7381,
        expected_votes=[23611, 19853, 0, 0],
    )


@pytest.mark.skip(reason="External IRV tests need fixing")
def test_maine_2018_cd2_general():
    """
    Maine 2018 Congress District 2 General Election
    Source: https://ranked.vote/us/me/2018/11/cd02/
    Data source: https://s3.amazonaws.com/ranked.vote-reports/us/me/2018/11/cd02/us_me_2018_11_cd02.normalized.csv.gz
    """
    run_election_test(
        file_name='us_me_2018_11_cd02.normalized.csv', expected_blank_votes=14706, expected_votes=[142440, 138931, 0, 0]
    )
