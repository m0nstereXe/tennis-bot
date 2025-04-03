from random import randint
import random

class AdaptiveStrategy:
    """
    Adaptive strategy using a shifted truncated-normal distribution over [0,3] to choose a mode:
      - Modes:
          "conservative": bet 5-35% of remaining points,
          "moderate": bet 25-65%,
          "aggressive": bet 55-90%.
      - On the first turn, a mode is chosen at random.
      - In a critical round (position == 5), 70% of the time choose aggressive, 
        30% choose a uniform bet between 1 and 5.
      - Otherwise, sample a value from a normal (mean 1.5, std 0.55, clamped to [0,3]),
        shift it by a factor based on the ratio (current_points/opponent_points),
        and map the result to a mode: [0,1) → conservative, [1,2) → moderate, [2,3] → aggressive.
      - Safety checks: if the bet leaves too few points (opponent_points > 1.5 * (current_points - bet)),
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
        return int(current_points * random.uniform(0.7, 0.85))
    
    def uniform_bet(self, current_points):
        return min(current_points, random.randint(1, 3))
    
    def sample_mode_value(self):
        sample = random.gauss(1.5, 0.55)
        return max(0, min(sample, 3))
    
    def choose_mode(self, current_points, opponent_points):
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
                if random.random() < 0.9:
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
                bet = max(int(bet * random.gauss(0.35, 0.05)), 0)
        if opponent_points < current_points:
            bet = min(bet, opponent_points + 1)
        if opponent_points > 0 and current_points / opponent_points > 2:
            bet = opponent_points + 1
        if opponent_points == 0:
            bet = 1
        
        return bet

hardcoded_strategy=AdaptiveStrategy()