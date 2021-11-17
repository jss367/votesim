def head_to_head(ballots, cand_a, cand_b):
    prefer_a = 0
    prefer_b = 0
    for ballot in ballots:
        for candidate in ballot.ranked_candidates:
            if candidate == cand_a:
                prefer_a += 1
                break
            elif candidate == cand_b:
                prefer_b += 1
                break
    print(f"Head-to-head Election Results:\n{cand_a}: {prefer_a}\n{cand_b}: {prefer_b}")
