import csv
import os

from votesim import Ballot, Candidate, instant_runoff_voting
from votesim.test_helpers import assert_list_almost_equal

TEST_FOLDER = "test_data/external_irv/"
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_PATH = os.path.join(THIS_DIR, os.pardir, TEST_FOLDER)


def parse_ballots_csv_file(file_name):
    """Parse CSV file containing ballot data and return candidates and ballots."""
    file_path = os.path.join(TEST_DATA_PATH, file_name)
    with open(file_path) as f:
        csv_data = list(csv.reader(f))[1:]  # Skip header

    candidates = {}
    ballots = []
    current_ranked_candidates = []
    current_ballot_id = None

    # Track ballot statistics for debugging
    total_ballots = 0
    skipped_undervotes = 0
    skipped_overvotes = 0

    for ballot_id, _, candidate_name in csv_data:
        # Create new ballot when ID changes
        if current_ballot_id is not None and ballot_id != current_ballot_id:
            if current_ranked_candidates:
                ballots.append(Ballot(current_ranked_candidates))
            else:
                # If we skipped all candidates for this ballot (due to under/overvotes),
                # add an empty ballot to maintain the blank vote count
                ballots.append(Ballot([]))
            total_ballots += 1
            current_ranked_candidates = []

        current_ballot_id = ballot_id

        # Track skipped votes
        if candidate_name == '$UNDERVOTE':
            skipped_undervotes += 1
            continue
        if candidate_name == '$OVERVOTE':
            skipped_overvotes += 1
            continue

        # Get or create candidate
        if candidate_name not in candidates:
            candidates[candidate_name] = Candidate(name=candidate_name)
        current_ranked_candidates.append(candidates[candidate_name])

    # Handle the last ballot
    if current_ranked_candidates:
        ballots.append(Ballot(current_ranked_candidates))
    else:
        ballots.append(Ballot([]))
    total_ballots += 1

    print(f"\nBallot Statistics for {file_name}:")
    print(f"Total ballots processed: {total_ballots}")
    print(f"Undervotes skipped: {skipped_undervotes}")
    print(f"Overvotes skipped: {skipped_overvotes}")
    print(f"Final ballot count: {len(ballots)}")

    return list(candidates.values()), ballots


def run_election_test(file_name, expected_blank_votes, expected_votes):
    """Run an election test case and verify results."""
    candidates, ballots = parse_ballots_csv_file(file_name)
    election_result = instant_runoff_voting(candidates, ballots)

    last_round = election_result.rounds[-1]

    # Add debugging information
    print(f"\nElection Results for {file_name}:")
    print(f"Expected blank votes: {expected_blank_votes}")
    print(f"Actual blank votes: {last_round.number_of_blank_votes}")
    print(f"Difference: {expected_blank_votes - last_round.number_of_blank_votes}")

    assert expected_blank_votes == last_round.number_of_blank_votes

    actual_votes = [result.number_of_votes for result in last_round.candidate_results]
    print(f"Expected votes: {expected_votes}")
    print(f"Actual votes: {actual_votes}")

    # Pass TestCase instance as first argument
    test_case = type('TestCase', (), {'assert_list_almost_equal': assert_list_almost_equal})()
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
