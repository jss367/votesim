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


def process_election_file(file_name: str) -> tuple[List[Ballot], List[Candidate], pd.DataFrame, int]:
    """Process election data file and return ballots and candidates"""
    data_dir = "tests/test_data/external_irv"
    file_path = os.path.join(data_dir, file_name)

    # Read the CSV file
    df = pd.read_csv(file_path)

    # Get unique candidates (excluding special values)
    unique_candidates = sorted(df[~df['choice'].str.startswith('$')]['choice'].unique())
    candidates = [Candidate(name) for name in unique_candidates]
    candidate_map = {name: candidate for name, candidate in zip(unique_candidates, candidates)}

    # Process ballots
    ballots = []

    # Count total unique ballot IDs to help determine undervotes
    total_unique_ballots = df['ballot_id'].nunique()

    for ballot_id, group in df.groupby('ballot_id'):
        # Sort by rank and get choices
        choices = group.sort_values('rank')['choice'].tolist()

        # Convert choices to candidates, removing duplicates and stopping at special values
        seen_candidates = set()
        ranked_candidates = []
        for choice in choices:
            if choice in candidate_map and choice not in seen_candidates:
                ranked_candidates.append(candidate_map[choice])
                seen_candidates.add(choice)
            elif choice.startswith('$'):
                break

        if ranked_candidates:  # Only add ballot if it has valid rankings
            ballots.append(Ballot(ranked_candidates))

    # Calculate blank votes as difference between total ballots and valid ballots
    blank_votes = total_unique_ballots - len(ballots)

    print(f"\nProcessed {len(df)} total rows")
    print(f"Found {len(candidates)} candidates:")
    for c in candidates:
        print(f"  - {c.name}")
    print(f"Total unique ballot IDs: {total_unique_ballots}")
    print(f"Created {len(ballots)} valid ballots")
    print(f"Calculated {blank_votes} blank votes")

    return ballots, candidates, df, blank_votes


def run_election_test(file_name: str, expected_blank_votes: int, expected_votes: List[int]) -> None:
    """Run election test with given file and expected results"""
    test_case = TestCase()

    # Process election data
    print(f"\nProcessing {file_name}")
    ballots, candidates, df, blank_votes = process_election_file(file_name)

    # Get ballot statistics
    unique_ballot_ids = df['ballot_id'].nunique()
    total_rows = len(df)

    # Print ballot statistics
    print(f"\nBallot Statistics for {file_name}:")
    print(f"Unique ballot IDs: {unique_ballot_ids}")
    print(f"Total rows in file: {total_rows}")
    print(f"Valid ballots created: {len(ballots)}")
    print(f"Number of candidates: {len(candidates)}")
    print(f"Blank votes: {blank_votes}")

    # Run election
    election_result = instant_runoff_voting(candidates, ballots)
    final_round = election_result.rounds[-1]
    actual_blank_votes = blank_votes  # Use counted blank votes
    actual_votes = [result.number_of_votes for result in final_round.candidate_results]

    # Print and verify results
    print(f"\nElection Results for {file_name}:")
    print("Final round candidates:")
    for result in final_round.candidate_results:
        print(f"  {result.candidate.name}: {result.number_of_votes}")
    print(f"Expected blank votes: {expected_blank_votes}")
    print(f"Actual blank votes: {actual_blank_votes}")
    print(f"Difference: {actual_blank_votes - expected_blank_votes}")
    print(f"Expected votes: {expected_votes}")
    print(f"Actual votes: {actual_votes}")

    # Assert results match expectations
    test_case.assert_list_almost_equal([expected_blank_votes], [actual_blank_votes])
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
