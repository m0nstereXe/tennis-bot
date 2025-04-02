import random
from random import randint
import numpy as np

# ---------------------------------------
# Original strategies

def hardcoded_strategy(role, current_points, opponent_points, overall_score, round_number):
    """
    Hardcoded strategy with ratio-based bet fraction ranges and a safety check:
      - On the first round, bet a small randomized amount based on 1 point.
      - In later rounds, generate a bet based on whether we're in a critical 
        (push-edge) situation or not. The bet fraction is chosen according to several 
        ratio intervals (current_points/opponent_points) with overlapping ranges.
      - If the suggested bet would leave us with remaining points such that 
        opponent_points > 1.5 * (current_points - bet), we re-generate the bet.
      - Finally, cap the bet if the opponent has fewer points (never betting more than 
        opponent_points+1), and if opponent_points is 0, default to a minimal bet.
    """
    if round_number == 1:
        bet = round(1 * random.uniform(1, 5))
        if opponent_points < current_points:
            bet = min(bet, opponent_points + 1)
        return bet

    ratio = current_points / opponent_points if opponent_points > 0 else float('inf')
    push_edge = ((role == "positive" and overall_score == 2) or 
                 (role == "negative" and overall_score == -2))

    def suggested_bet():
        local_act = random.random()
        if push_edge:
            if ratio >= 1:
                if ratio > 1.5:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.40, 0.65
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.60, 0.85
                    else:
                        lower_bound, upper_bound = 0.80, 0.95
                elif ratio > 1.25:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.35, 0.60
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.55, 0.80
                    else:
                        lower_bound, upper_bound = 0.75, 0.90
                elif ratio > 1.1:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.25, 0.50
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.45, 0.70
                    else:
                        lower_bound, upper_bound = 0.65, 0.85
                elif ratio > 1.05:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.15, 0.40
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.35, 0.60
                    else:
                        lower_bound, upper_bound = 0.55, 0.75
                else:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.05, 0.35
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.25, 0.75
                    else:
                        lower_bound, upper_bound = 0.40, 0.85
            else:
                effective = 2 if ratio == 0 else (1 / ratio)
                if effective > 1.5:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.05, 0.15
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.15, 0.30
                    else:
                        lower_bound, upper_bound = 0.30, 0.45
                elif effective > 1.25:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.08, 0.18
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.18, 0.33
                    else:
                        lower_bound, upper_bound = 0.33, 0.48
                elif effective > 1.1:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.10, 0.20
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.20, 0.35
                    else:
                        lower_bound, upper_bound = 0.35, 0.50
                else:
                    if local_act < 0.3:
                        lower_bound, upper_bound = 0.15, 0.25
                    elif local_act < 0.8:
                        lower_bound, upper_bound = 0.25, 0.40
                    else:
                        lower_bound, upper_bound = 0.40, 0.55
            return int(current_points * random.uniform(lower_bound, upper_bound))
        else:
            if ratio >= 1:
                if ratio > 1.5:
                    lower, upper = 0.40, 0.85
                elif ratio > 1.25:
                    lower, upper = 0.35, 0.80
                elif ratio > 1.1:
                    lower, upper = 0.30, 0.75
                elif ratio > 1.05:
                    lower, upper = 0.25, 0.70
                else:
                    lower, upper = 0.20, 0.65
            else:
                effective = 2 if ratio == 0 else 1 / ratio
                if effective > 1.5:
                    lower, upper = 0.05, 0.15
                elif effective > 1.25:
                    lower, upper = 0.10, 0.20
                elif effective > 1.1:
                    lower, upper = 0.15, 0.25
                elif effective > 1.05:
                    lower, upper = 0.20, 0.30
                else:
                    lower, upper = 0.25, 0.35
            return int(current_points * random.uniform(lower, upper))
    
    max_attempts = 100
    attempt = 0
    bet = suggested_bet()
    while attempt < max_attempts:
        remaining = current_points - bet
        if remaining > 0 and opponent_points > 2.5 * remaining:
            bet = suggested_bet()
            attempt += 1
        else:
            break
    if attempt == max_attempts:
        bet = 1

    if opponent_points <= current_points:
        bet = min(bet, opponent_points + 1)
    if opponent_points == 0:
        bet = 1

    return bet

# Adaptive strategy (beats hardcoded ~86% of the time)

class AdaptiveStrategy:
    """
    Adaptive strategy using a shifted truncated-normal distribution over [0,3] to choose a mode:
      - Modes:
          "conservative": bet 5-10% of remaining points,
          "moderate": bet 10-20%,
          "aggressive": bet 20-40%.
      - On the first turn, a mode is chosen at random.
      - In a critical round (overall_score == 2 for positive or -2 for negative),
        70% of the time choose aggressive, 30% choose a uniform bet between 1 and 5.
      - Otherwise, sample a value from a normal (mean 1.5, std 0.55, clamped to [0,3]),
        shift it by a factor based on the ratio (our_points/opponent_points),
        and map the result to a mode: [0,1] → conservative, [1,2] → moderate, [2,3] → aggressive.
      - Safety checks: if the bet leaves too few points (opponent_points > 1.5*(current_points - bet)),
        reduce the bet; also cap bet to opponent_points+1 when opponent is behind.
    """
    def __init__(self):
        self.mode = None
    
    def reset(self):
        self.mode = None

    def conservative_bet(self, current_points):
        return int(current_points * random.uniform(0.05, 0.35))

    def moderate_bet(self, current_points):
        return int(current_points * random.uniform(0.25, 0.65))
    
    def aggressive_bet(self, current_points):
        return int(current_points * random.uniform(0.55, 0.9))
    
    def uniform_bet(self, current_points):
        return min(current_points, random.randint(1, 5))
    
    def sample_mode_value(self):
        sample = random.gauss(1.5, 0.55)
        return max(0, min(sample, 3))
    
    def choose_mode(self, role, current_points, opponent_points, overall_score):
        ratio = current_points / opponent_points if opponent_points > 0 else float('inf')
        base = self.sample_mode_value()
        shift_factor = 1.0
        if ratio > 1:
            shifted = base - shift_factor * (ratio - 1)
        elif ratio < 1:
            shifted = base + shift_factor * (1 - ratio)
        else:
            shifted = base
        shifted = max(0, min(shifted, 3))
        if shifted < 1:
            return "conservative"
        elif shifted < 2:
            return "moderate"
        else:
            return "aggressive"
    
    def __call__(self, role, current_points, opponent_points, overall_score, round_number):
        push_edge = ((role == "positive" and overall_score == 2) or 
                     (role == "negative" and overall_score == -2))
        
        if round_number == 1:
            self.mode = "conservative"
        else:
            if push_edge:
                if random.random() < 0.7:
                    self.mode = "aggressive"
                else:
                    self.mode = "uniform"
            else:
                self.mode = self.choose_mode(role, current_points, opponent_points, overall_score)
        
        if self.mode == "conservative":
            bet = self.conservative_bet(current_points)
        elif self.mode == "moderate":
            bet = self.moderate_bet(current_points)
        elif self.mode == "aggressive":
            bet = self.aggressive_bet(current_points)
        elif self.mode == "uniform":
            bet = self.uniform_bet(current_points)
        else:
            bet = self.conservative_bet(current_points)
        
        remaining = current_points - bet
        if remaining > 0 and opponent_points > 1.5 * remaining:
            if not push_edge:
                bet = int(bet * random.gauss(0.3, 0.15))
        if opponent_points < current_points:
            bet = min(bet, opponent_points + 1)
        if opponent_points > 0 and current_points / opponent_points > 3:
            bet = opponent_points + 1
        if opponent_points == 0:
            bet = 1
        
        return bet

def random_strategy(role, current_points, opponent_points, overall_score, round_number):
    return 0 if current_points == 0 else random.randint(1, current_points)

def human_strategy(role, current_points, opponent_points, overall_score, round_number):
    while True:
        try:
            bet = int(input(f"Enter your bet (0 to {current_points}) for round {round_number}: "))
            if 0 <= bet <= current_points:
                return bet
            else:
                print("Invalid bet amount. Please try again.")
        except ValueError:
            print("Invalid input. Please enter an integer.")

# ---------------------------------------
# New strategy functions (fourth option)
# These use a different accounting system. Here we assume the new strategy functions
# expect: bot_coins, opponent_coins, and position.
# We define new_strat_base, strat_wrapper, and new_strat.
# Then we define new_strategy to match our (role, current_points, opponent_points, overall_score, round_number) signature.
    
def new_strat_base(bc: int, oc: int, p: int) -> int:
    delta = bc - oc 
    d = 6 - p
    p = p - 3
    if delta > 0 and oc == 0:
        return 1
    c = bc // d 
    if c > oc:
        return min(oc + 1, c)
    if p == 0:
        if oc == 64:
            r = randint(0,10)
            if r <= 3:
                return 0
            elif r == 4:
                return randint(0,4)
            elif r == 5:
                return randint(0,8)
            elif r == 6:
                return randint(0,15)
            else:
                return randint(15,21)
        x = randint(0,10)
        if delta > 0 and 5 * delta <= bc and randint(0,1):
            return 2 * delta 
        if x <= 1:
            return 0
        if x <= 6 and oc >= 55:
            return randint(10,20)
        if x <= 6 and oc >= 40:
            return randint(5,10)
        elif x <= 9 and x >= 25:
            return min(abs(delta) + randint(-10,10), bc // 2)
        return randint(0, bc // 3 + (bc % 3 != 0))
    elif p == 1:
        x = randint(0, 10)
        if x <= 4:
            if oc >= 40:
                return randint(10,20)
            if oc >= 20:
                return randint(5,10)
            return randint(0, min(8, bc))
        if x <= 8:
            return randint(0, bc // 4 + (bc % 4 != 0))
        return randint(0, abs(delta))
    elif p == -1:
        x = randint(0, 10)
        if x <= 4:
            if oc >= 40:
                return randint(10,20)
            if oc >= 20:
                return randint(5,10)
            return randint(0, min(8, bc))
        if x <= 8:
            return randint(0, bc // 4 + (bc % 4 != 0))
        return randint(0, abs(delta))
    elif p == -2:
        x = randint(0,10)
        if bc > oc and x <= 1:
            return oc + 1
        if x <= 6:
            return min(bc, randint(delta, delta + 5))
        if x == 10:
            return min(bc, 1)
        return randint(bc // 2 + (bc & 1), bc)
    elif p == 2:
        x = randint(0,10)
        if x <= 3:
            return bc
        if x <= 6:
            return bc // 2
        if x <= 9:
            return 0
        return randint(0, bc)

def strat_wrapper(bc: int, oc: int, p: int) -> int:
    ub = oc + 1
    ub = min(ub, bc)
    res = min(new_strat_base(bc, oc, p), ub)
    res = max(res, 0)
    return res 

def new_strat(bc: int, oc: int, p: int) -> int:
    return strat_wrapper(bc, oc, p)

def new_strategy(role, current_points, opponent_points, overall_score, round_number):
    """
    Wraps the new strategy functions to match our standard signature.
    We map overall_score (range -3 to 3) to a position by adding 3,
    so that position ranges from 0 to 6.
    """
    position = overall_score + 3
    return new_strat(current_points, opponent_points, position)

# ---------------------------------------
# Game simulation functions

def play_game(strategy_positive, strategy_negative, verbose=True, max_rounds=None):
    pos_points = 64
    neg_points = 64
    overall_score = 0
    round_number = 1

    if hasattr(strategy_positive, 'reset'):
        strategy_positive.reset()
    if hasattr(strategy_negative, 'reset'):
        strategy_negative.reset()
    
    while overall_score not in [-3, 3] and not (pos_points == 0 and neg_points == 0):
        if max_rounds is not None and round_number > max_rounds:
            break

        if verbose:
            print(f"\nRound {round_number}:")
            print(f"Overall score: {overall_score}")
            print(f"Positive points: {pos_points} | Negative points: {neg_points}")
        
        bet_positive = strategy_positive("positive", pos_points, neg_points, overall_score, round_number)
        bet_negative = strategy_negative("negative", neg_points, pos_points, overall_score, round_number)
        
        if verbose:
            print(f"Positive bets: {bet_positive}")
            print(f"Negative bets: {bet_negative}")
        
        pos_points -= bet_positive
        neg_points -= bet_negative
        
        if bet_positive > bet_negative:
            overall_score -= 1
            if verbose:
                print("Positive wins the round (overall score decreases by 1).")
        elif bet_positive < bet_negative:
            overall_score += 1
            if verbose:
                print("Negative wins the round (overall score increases by 1).")
        else:
            if verbose:
                print("Tie round (overall score unchanged).")
        
        round_number += 1

    if overall_score == -3:
        winner = "positive"
    elif overall_score == 3:
        winner = "negative"
    else:
        if overall_score > 0:
            winner = "negative"
        elif overall_score < 0:
            winner = "positive"
        else:
            winner = "tie"
    
    if verbose:
        print("\nGame over!")
        print(f"Final overall score: {overall_score}")
        print(f"Remaining points -> Positive: {pos_points}, Negative: {neg_points}")
        if winner == "tie":
            print("The game is a tie!")
        else:
            print(f"The winner is the {winner} player!")
    return winner

def simulate_games(num_games, strategy_positive, strategy_negative, max_rounds=100):
    results = {"positive": 0, "negative": 0, "tie": 0}
    for i in range(num_games):
        winner = play_game(strategy_positive, strategy_negative, verbose=False, max_rounds=max_rounds)
        results[winner] += 1
    return results

# ---------------------------------------
# Main function with fourth mode added

def main():
    print("Welcome to the Points Game!")
    print("Choose a mode:")
    print("1: Play against the adaptive strategy")
    print("2: Test performance of the adaptive strategy vs a uniform random player")
    print("3: Test performance of the adaptive strategy vs hardcoded strategy")
    print("4: Test performance of the adaptive strategy vs new strategy")
    mode = input("Enter mode (1, 2, 3, or 4): ").strip()

    if mode == "1":
        role_choice = input("Choose your role (positive/negative): ").strip().lower()
        if role_choice not in ["positive", "negative"]:
            print("Invalid role. Defaulting to 'positive'.")
            role_choice = "positive"
        
        if role_choice == "positive":
            pos_strategy = human_strategy
            neg_strategy = AdaptiveStrategy()
        else:
            pos_strategy = AdaptiveStrategy()
            neg_strategy = human_strategy
        
        play_game(pos_strategy, neg_strategy, verbose=True)
    
    elif mode == "2":
        try:
            num_games = int(input("Enter the number of games to simulate: "))
        except ValueError:
            print("Invalid number. Defaulting to 1000 games.")
            num_games = 1000
        
        print("\nSimulating games: Adaptive strategy (as positive) vs Uniform Random (as negative)...")
        adaptive = AdaptiveStrategy()
        results = simulate_games(num_games, adaptive, random_strategy, max_rounds=100)
        print("\nSimulation results:")
        print(f"Games simulated: {num_games}")
        print(f"Adaptive strategy wins (as positive): {results['positive']}")
        print(f"Uniform random wins (as negative): {results['negative']}")
        print(f"Ties: {results['tie']}")
    
    elif mode == "3":
        try:
            num_games = int(input("Enter the number of games to simulate: "))
        except ValueError:
            print("Invalid number. Defaulting to 1000 games.")
            num_games = 1000
        
        print("\nSimulating games: Adaptive strategy (as positive) vs Hardcoded strategy (as negative)...")
        adaptive = AdaptiveStrategy()
        results = simulate_games(num_games, adaptive, hardcoded_strategy, max_rounds=100)
        print("\nSimulation results:")
        print(f"Games simulated: {num_games}")
        print(f"Adaptive strategy wins (as positive): {results['positive']}")
        print(f"Hardcoded strategy wins (as negative): {results['negative']}")
        print(f"Ties: {results['tie']}")
    
    elif mode == "4":
        try:
            num_games = int(input("Enter the number of games to simulate: "))
        except ValueError:
            print("Invalid number. Defaulting to 1000 games.")
            num_games = 1000
        
        print("\nSimulating games: Adaptive strategy (as positive) vs New strategy (as negative)...")
        adaptive = AdaptiveStrategy()
        results = simulate_games(num_games, adaptive, new_strategy, max_rounds=100)
        print("\nSimulation results:")
        print(f"Games simulated: {num_games}")
        print(f"Adaptive strategy wins (as positive): {results['positive']}")
        print(f"New strategy wins (as negative): {results['negative']}")
        print(f"Ties: {results['tie']}")

    elif mode=="custom":
        try:
            num_games = int(input("Enter the number of games to simulate: "))
        except ValueError:
            print("Invalid number. Defaulting to 1000 games.")
            num_games = 1000
        
        print("\nSimulating games: Adaptive strategy (as positive) vs New strategy (as negative)...")
        results = simulate_games(num_games, random_strategy, new_strategy, max_rounds=100)
        print("\nSimulation results:")
        print(f"Games simulated: {num_games}")
        print(f"Adaptive strategy wins (as positive): {results['positive']}")
        print(f"New strategy wins (as negative): {results['negative']}")
        print(f"Ties: {results['tie']}")
    
    else:
        print("Invalid mode selection.")

if __name__ == "__main__":
    main()
