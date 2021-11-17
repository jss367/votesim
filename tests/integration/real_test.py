import re
from votesim import *

file = "test_data/JLburl09.txt"

with open(file, "r") as f:
    a = f.readlines()

regex = "(\d+): ((\w>?)+)"

kiss = Candidate("Bob Kiss")
wright = Candidate("Kurt Wright")
montroll = Candidate("Andy Montroll")
smith = Candidate("Dan Smith")
simpson = Candidate("James Simpson")
write_in = Candidate("Write-in")

candidates = [kiss, wright, montroll, smith, simpson, write_in]

cand_map = {"K": kiss, "M": montroll, "N": simpson, "H": smith, "W": wright, "R": write_in}

all_ballots = []
for i in range(18, 395):
    m = re.search(regex, a[i])
    num_ballots = int(m.group(1))
    ranked_cands = m.group(2).split(">")
    ranked_can_list = []
    for c in ranked_cands:
        ranked_can_list.append(cand_map[c])
    my_bal = Ballot(ranked_can_list)
    all_ballots.extend([my_bal] * num_ballots)

election_result = instant_runoff_voting(candidates, all_ballots)
election_result.get_winners()
print(election_result)
