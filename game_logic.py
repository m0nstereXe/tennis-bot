from random import randint

def generate_game_display(game) -> str:
    """
    Returns a string with an emoji-based display of the cups and the ball position.
    If the ball has fallen off the left or right side, show a special graphic.
    """

    if game.active == False and game.check_winner()=="Player2":
        cups_str = "🎾  ⚪  ⚪  ⚪  ⚪  ⚪   **(off the left side!)**"
    elif game.active==False and game.check_winner()=="Player1":
        cups_str = "⚪  ⚪  ⚪  ⚪  ⚪  🎾   **(off the right side!)**"
    else:
        cups = ["⚪", "⚪", "⚪", "⚪", "⚪"]
        p = game.p 
        p = 5 - p + 1
        cups[p - 1] = "🎾"
        cups_str = " ".join(cups)

    info_str = (
        f"**Player1 Coins**: {game.a} | **Bot Coins**: {game.b}\n"
        f"**Ball Position**: {game.p - 3}\n"
    )

    return f"{cups_str}\n{info_str}"


class TennisGame:
    def __init__(self, player1_id, player2_id):
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.a = 64
        self.b = 64
        self.p = 3
        self.active = True

    def play_round(self, x, y):
        if x > y:
            if self.p > 1:
                self.p -= 1
            else:
                self.active = False
        elif y > x:
            if self.p < 5:
                self.p += 1
            else:
                self.active = False

        self.a -= x
        self.b -= y

        if self.a < 0: 
            self.a = 0
        if self.b < 0: 
            self.b = 0

        if (self.a <= 0 and self.b <= 0) or not (1 <= self.p <= 5):
            self.active = False

    def check_winner(self):
        """
        Returns:
            'Player1' if P1 wins
            'Player2' if P2 wins
            'Tie' if tie
            None if game not finished
        """
        if self.active:
            return None
        if self.p < 1:
            return "Player1"
        if self.p > 5:
            return "Player2"
        if self.p == 3:
            return "Tie"
        else:
            if self.p == 4 or self.p == 5:
                return "Player2"
            else:
                return "Player1"