"""Tests for external IRV election cases"""

import os
from dataclasses import dataclass
from typing import Any, List, Optional

import pandas as pd

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
    """Analyze patterns in the ballot data to understand invalidation rules"""
    print("\nBallot Pattern Analysis:")

    # Print statistics for each ballot_id's ranking pattern
    pattern_counts = {}
    for ballot_id, group in df.groupby('ballot_id'):
        choices = group.sort_values('rank')['choice'].tolist()
        pattern = []
        for choice in choices:
            if choice.startswith('$'):
                pattern.append(choice[1:])  # Remove $ for readability
            else:
                pattern.append('VOTE')
        pattern = tuple(pattern)
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    print("\nMost common ballot patterns:")
    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
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
        print(f"  {val}: {count} occurrences")

    # Analyze ballot patterns
    analyze_ballot_patterns(df)

    # Get unique candidates (excluding special values)
    unique_candidates = sorted(df[~df['choice'].str.startswith('$')]['choice'].unique())
    candidates = [Candidate(name) for name in unique_candidates]
    candidate_map = {name: candidate for name, candidate in zip(unique_candidates, candidates)}

    # Process ballots and count different types of invalid votes
    ballots = []
    total_invalid = 0
    skipped_ballots = set()
    expected_ranks = list(range(1, df['rank'].max() + 1))

    # First pass: identify invalid ballots
    for ballot_id, group in df.groupby('ballot_id'):
        group_sorted = group.sort_values('rank')
        choices = group_sorted['choice'].tolist()
        ranks = group_sorted['rank'].tolist()

        # Check if ballot has overvote
        if any(c == '$OVERVOTE' for c in choices):
            skipped_ballots.add(ballot_id)
            total_invalid += 1
            continue

        # Check if ballot is all undervotes
        if all(c == '$UNDERVOTE' for c in choices):
            skipped_ballots.add(ballot_id)
            total_invalid += 1
            continue

        # Check if ranks are continuous (no gaps)
        if ranks != expected_ranks[: len(ranks)]:
            skipped_ballots.add(ballot_id)
            total_invalid += 1
            continue

        # Check for undervotes in middle of valid choices
        valid_found = False
        undervote_found = False
        for choice in choices:
            if not choice.startswith('$'):
                valid_found = True
                if undervote_found:
                    skipped_ballots.add(ballot_id)
                    total_invalid += 1
                    break
            elif choice == '$UNDERVOTE':
                undervote_found = True
                if valid_found:
                    skipped_ballots.add(ballot_id)
                    total_invalid += 1
                    break

    # Second pass: create valid ballots
    for ballot_id, group in df.groupby('ballot_id'):
        if ballot_id in skipped_ballots:
            continue

        ranked_candidates = []
        seen_candidates = set()

        for choice in group.sort_values('rank')['choice']:
            if not choice.startswith('$'):
                if choice in candidate_map and choice not in seen_candidates:
                    ranked_candidates.append(candidate_map[choice])
                    seen_candidates.add(choice)

        if ranked_candidates:
            ballots.append(Ballot(ranked_candidates))
        else:
            total_invalid += 1

    print(f"\nProcessed {len(df)} total rows")
    print(f"Found {len(candidates)} candidates:")
    for c in candidates:
        print(f"  - {c.name}")
    print(f"Total unique ballot IDs: {df['ballot_id'].nunique()}")
    print(f"Created {len(ballots)} valid ballots")
    print(f"Total invalid/blank votes: {total_invalid}")

    return ballots, candidates, df, total_invalid


def run_election_test(file_name: str, expected_blank_votes: int, expected_votes: List[int]) -> None:
    """Run election test with given file and expected results"""
    test_case = TestCase()

    # Process election data
    print(f"\nProcessing {file_name}")
    ballots, candidates, df, blank_votes = process_election_file(file_name)

    # Print ballot statistics
    print(f"\nBallot Statistics for {file_name}:")
    print(f"Total unique ballots: {df['ballot_id'].nunique()}")
    print(f"Valid ballots: {len(ballots)}")
    print(f"Invalid/blank votes: {blank_votes}")
    print(f"Candidates ({len(candidates)}):")
    for c in candidates:
        print(f"  - {c.name}")

    # Run election
    election_result = instant_runoff_voting(candidates, ballots)
    final_round = election_result.rounds[-1]
    actual_votes = [result.number_of_votes for result in final_round.candidate_results]

    # Print and verify results
    print(f"\nElection Results for {file_name}:")
    print("Final round:")
    for result in final_round.candidate_results:
        print(f"  {result.candidate.name}: {result.number_of_votes:.1f}")
    print(f"\nExpected blank votes: {expected_blank_votes}")
    print(f"Actual blank votes: {blank_votes}")
    print(f"Difference: {blank_votes - expected_blank_votes}")
    print(f"Expected votes: {expected_votes}")
    print(f"Actual votes: {[v for v in actual_votes]}")

    # Assert results match expectations
    test_case.assert_list_almost_equal([expected_blank_votes], [blank_votes])
    test_case.assert_list_almost_equal(expected_votes, actual_votes)


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


def test_maine_2018_cd2_general():
    """
    Maine 2018 Congress District 2 General Election
    Source: https://ranked.vote/us/me/2018/11/cd02/
    Data source: https://s3.amazonaws.com/ranked.vote-reports/us/me/2018/11/cd02/us_me_2018_11_cd02.normalized.csv.gz
    """
    run_election_test(
        file_name='us_me_2018_11_cd02.normalized.csv', expected_blank_votes=14706, expected_votes=[142440, 138931, 0, 0]
    )
