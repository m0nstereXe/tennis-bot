from random import randint
import random
"""
Ryolo tennis strategy
"""
# Define a helper function that generates a suggested bet based on the branch.
def suggested_bet(ratio, push_edge, current_points):
    local_act = random.random()
    if push_edge:
        # Critical round branch with granular ranges.
        if ratio >= 1:  # We're ahead.
            if ratio >= 1.5:
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.40, 0.60
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.60, 0.85
                else:
                    lower_bound, upper_bound = 0.85, 0.95
            elif ratio >= 1.25:
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.30, 0.50
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.50, 0.75
                else:
                    lower_bound, upper_bound = 0.75, 0.90
            elif ratio >= 1.1:
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.20, 0.40
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.40, 0.65
                else:
                    lower_bound, upper_bound = 0.65, 0.80
            else:  # ratio between 1 and 1.1
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.10, 0.30
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.30, 0.50
                else:
                    lower_bound, upper_bound = 0.50, 0.65
        else:
            # We're behind. Use symmetric ranges based on the reciprocal.
            if ratio <= 1/1.5:  # effective ratio >= 1.5.
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.05, 0.15
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.15, 0.30
                else:
                    lower_bound, upper_bound = 0.30, 0.45
            elif ratio <= 1/1.25:  # effective ratio >= 1.25.
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.05, 0.20
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.20, 0.35
                else:
                    lower_bound, upper_bound = 0.35, 0.50
            elif ratio <= 1/1.1:  # effective ratio >= 1.1.
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.05, 0.25
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.25, 0.40
                else:
                    lower_bound, upper_bound = 0.40, 0.55
            else:
                if local_act < 0.3:
                    lower_bound, upper_bound = 0.05, 0.30
                elif local_act < 0.8:
                    lower_bound, upper_bound = 0.30, 0.45
                else:
                    lower_bound, upper_bound = 0.45, 0.60
        return int(current_points * random.uniform(lower_bound, upper_bound))
    else:
        # Non-critical branch.
        if ratio >= 1:  # We're ahead.
            if ratio >= 1.5:
                lower, upper = 0.40, 0.80
            elif ratio >= 1.25:
                lower, upper = 0.35, 0.75
            elif ratio >= 1.1:
                lower, upper = 0.30, 0.70
            else:
                lower, upper = 0.25, 0.65
        else:
            # When behind.
            if ratio <= 1/1.5:
                lower, upper = 0.05, 0.20
            elif ratio <= 1/1.25:
                lower, upper = 0.10, 0.25
            elif ratio <= 1/1.1:
                lower, upper = 0.15, 0.30
            else:
                lower, upper = 0.20, 0.35
        return int(current_points * random.uniform(lower, upper))

def hardcoded_strategy(current_points, opponent_points, position, first_round):
    """
    Hardcoded strategy with ratio-based bet fraction ranges and a safety check:
      - On the first round, bet a small randomized amount based on 1 point.
      - In later rounds, first generate a bet based on whether we're in a critical 
        (push-edge) situation or not. The bet fraction is chosen according to several 
        ratio intervals (current_points/opponent_points), with symmetric ranges when behind.
      - Then, if making that bet would leave us with remaining points (current_points - bet)
        such that the opponent's points are more than 2.5 times our remaining points,
        we re-generate the bet.
      - Finally, we cap the bet if the opponent has fewer points (never betting more than
        opponent_points+1), and if the opponent has 0, we default to a minimal bet.
    """
    # Opening move: always bet a small randomized amount in round 1.
    if first_round:
        bet = round(1 * random.uniform(1, 5))
        if opponent_points < current_points:
            bet = min(bet, opponent_points + 1)
        return bet

    # Compute ratio (if opponent_points is 0, use infinity).
    ratio = current_points / opponent_points if opponent_points > 0 else float('inf')

    # Determine if we're in a "push-edge" situation.
    push_edge = (position==5)

    # Generate a bet that satisfies our safety condition:
    # "If making this bet leaves us with remaining points such that the opponent has > 2.5x our remaining points,
    # then re-generate the bet."
    max_attempts = 100
    attempt = 0
    bet = suggested_bet(ratio=ratio, push_edge=push_edge, current_points=current_points)
    while attempt < max_attempts:
        remaining = current_points - bet
        # Only check the condition if we would have some points left.
        if remaining > 0 and opponent_points > 1.5 * remaining:
            bet = suggested_bet(ratio=ratio, push_edge=push_edge, current_points=current_points)  # regenerate the bet
            attempt += 1
        else:
            break
    if attempt == max_attempts:
        # Fallback if we couldn't find a safe bet.
        bet = 1

    # Additional cap: if the opponent's points are less than or equal to ours, never bet more than opponent_points+1.
    if opponent_points <= current_points:
        bet = min(bet, opponent_points + 1)

    if opponent_points == 0:
        bet = 1

    return bet