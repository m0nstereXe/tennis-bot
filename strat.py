from random import randint

def bot_strategy(bot_coins: int, opponent_coins: int, position: int) -> int:
    if bot_coins==64 and opponent_coins==64 and randint(0,10)==0:
        return 21 #hardcoded 21 :>

    if(bot_coins and opponent_coins == 0):
        return 1

    delta = bot_coins - opponent_coins
    d = 6 - position
    c = bot_coins // d
    ub = opponent_coins + 1
    if c > opponent_coins:
        return min(ub, c)

    if delta > 10 and randint(0, 1):
        return min(ub, randint(delta, min(bot_coins, delta + 5)))

    if position == 2: 
        if delta > 0 and randint(0, 1): 
            return min(ub, delta)
        return min(ub, randint(0, bot_coins // 4 + (bot_coins % 4 != 0)))
    elif position == 1:
        if(randint(0,1) and ub <= bot_coins):
            return ub
        if(randint(0,1) and 0<=ub-5<=bot_coins):
            return ub-5
        return min(ub, randint(min(bot_coins, 5), bot_coins))
    elif position > 3:
        if position == 5 and randint(0, 3) == 0:  # 25% chance to go crazy style
            return min(ub, bot_coins)
        return min(ub, randint(0, bot_coins // 7 + (bot_coins % 7 != 0)))  # play very safe
    else:  # this is the three branch
        if bot_coins > opponent_coins and randint(0, 1) == 0:  # 50%
            return min(ub, 0)
        else:
            return min(ub, randint(0, min(8, bot_coins)))

def new_strat_base(bc: int, oc :int, p:int) -> int:
    delta = bc - oc 
    d = 6 - p
    p = p - 3
    
    if delta>0 and oc == 0: #trivial forced move
        return 1

    c = bc // d 
    if c > oc: return c
    
    if p == 0: #bot tie
        if oc == 64: #opening move
            r = randint(0,10)
            if r <= 3: return 0
            elif r == 4: return randint(0,4)
            elif r == 5: return randint(0,8)
            elif r == 6: return randint(0,15)
            else: return randint(15,21) #aggressive open
        x = randint(0,10)

        if delta>0 and 5*delta <= bc and randint(0,1): return 2*delta 

        if x <= 1: return 0
        if x<=6 and oc>=55: return randint(10,20)
        if x<=6 and oc >= 40: return randint(5,10)
        elif x<=9 and x >= 25: return min(abs(delta) + randint(-10,10),bc//2)

        return randint(0,bc//3 + (bc%3 != 0)) 
    elif p == 1: 
        x = randint(0, 10)   
        if x<=4: 
            if oc>= 40: return randint(10,20)
            if(oc >= 20): return randint(5,10)
            return randint(0,min(8,bc))
        if x <= 8:
            return randint(0, bc // 4 + (bc % 4 != 0))
        return randint(0,abs(delta))
    elif p == -1:
        x = randint(0, 10)   
        if x<=4: 
            if oc>= 40: return randint(10,20)
            if(oc >= 20): return randint(5,10)
            return randint(0,min(8,bc))
        if x <= 8:
            return randint(0, bc // 4 + (bc % 4 != 0))
        return randint(0,abs(delta))
    elif p == -2: #bot losing by 2
        x = randint(0,10)
        if bc>oc and x<=1: return oc+1
        if x<=6: return min(bc,randint(delta,delta+5))
        if x == 10: return min(bc,1)
        return randint(bc //2 + (bc&1), bc)

    elif p == 2: #bot winning by 2
        x = randint(0,10)
        if x <= 3: return bc #crazy style go for the kill
        if x<= 6: return bc//2
        if x<= 9: return 0

        return randint(0,bc)

def strat_wrapper(bc: int, oc :int, p:int) -> int:
    ub=oc+1
    ub = min(ub,bc)
    res =min(new_strat_base(bc,oc,p),ub)
    res = max(res,0)
    return res 

def new_strat(bc: int, oc :int, p:int) -> int:
    return strat_wrapper(bc,oc,p)

def final_strategy(bot_coins: int, opp_coins: int, pos: int) -> int:
    """
    A randomized strategy that chooses from a weighted list of candidate bets
    based on the game state (coin margin, ball position).
    
    Args:
        bot_coins (int): Number of coins the bot has left.
        opp_coins (int): Number of coins the opponent has left.
        pos (int): Ball position (1..5). 
                   - pos=3 is center; pos=1 or pos=5 is extreme edges.
                   
    Returns:
        int: A bet between 0 and bot_coins (inclusive).
    """
    
    # If we literally have no coins, we have no choice:
    if bot_coins <= 0:
        return 0

    # Margin in coins: positive means we have more coins, negative means fewer.
    margin = bot_coins - opp_coins
    
    # The offset from center: pos=3 => offset=0, pos=5 => offset=+2, pos=1 => offset=-2
    offset = pos - 3
    
    # We'll build a list of (bet_amount, weight). We'll pick randomly based on the weights.
    candidates = []

    # Helper to add a candidate bet safely (clamped to 0..bot_coins)
    def add_candidate(bet, w):
        bet_clamped = max(0, min(bet, bot_coins))
        if w > 0 and bet_clamped >= 0:
            candidates.append((bet_clamped, w))

    # --------------------------------------------------
    # EXTREME POSITIONS: pos=5 or pos=1  -> about to win/lose
    # --------------------------------------------------
    if offset == 2:
        # pos=5 => one push off to the right means we (as Player2) win.
        # Threaten a big bet to guarantee the push, but add variety so it's not 100% the same.
        # Opponent might bet up to opp_coins, so opp_coins+1 is guaranteed to win the push if we can afford it.

        # High chance: do opp_coins+1 (the forced win)
        add_candidate(opp_coins + 1, 70)  # 70 weight

        # Some chance to bet 0 or a small number to keep them guessing:
        add_candidate(0, 10)
        add_candidate(5, 20)  # Slightly higher small bet

    elif offset == -2:
        # pos=1 => if the opponent wins the next push, we lose (ball goes off left side).
        # We need to outbid them frequently, but add small random seeds so it's not always the same.
        add_candidate(opp_coins + 1, 60)  # mostly we do a big bet to avoid immediate loss
        add_candidate(opp_coins, 20)      # or nearly big
        add_candidate(0, 5)               # a rare bluff
        add_candidate(10, 15)             # maybe a mid-range in case opponent tries to save coins

    else:
        # --------------------------------------------------
        # NON-EXTREME POSITIONS (pos=2,3,4)
        # --------------------------------------------------

        # Next, factor in the coin margin to shape how big or small we want to bet.
        if margin > 20:
            # We have a LARGE coin lead. We can bet small frequently to force the opponent to overspend
            # if they want to move the ball. But include some bigger bets occasionally as a threat.
            add_candidate(0, 20)
            add_candidate(2, 30)
            add_candidate(5, 30)
            add_candidate(opp_coins + 1, 10)  # random threat
            add_candidate(bot_coins, 10)      # big push sometimes
        elif margin < -20:
            # We have a LARGE deficit in coins. We might need big bets more often to swing momentum
            # or else we won't keep up if we stay small.
            add_candidate(opp_coins + 1, 25)  # a frequent all-in
            add_candidate(bot_coins, 25)      # all coins
            add_candidate(max(0, opp_coins - 2), 20)
            add_candidate(5, 10)
            add_candidate(0, 20)              # sometimes we do nothing, hoping opponent overspends
        else:
            # Balanced margin => we do a mixture of small, medium, and bigger bets
            # depending on which side the ball is leaning (offset).
            if offset > 0:
                # Ball is on our side (pos > 3). We can threaten with small bets often, 
                # but occasionally do bigger pushes to keep them guessing.
                add_candidate(0, 25)
                add_candidate(3, 25)
                add_candidate(6, 20)
                add_candidate(opp_coins + 1, 10)
                add_candidate(bot_coins, 5)  # rare big push
                add_candidate(1, 15)         # pepper in a 1
            elif offset < 0:
                # Ball is on the opponent’s side (pos < 3). We often want mid-sized to bigger bets to shift it.
                add_candidate(0, 20)               # sometimes do zero
                add_candidate(5, 30)
                add_candidate(10, 25)
                add_candidate(opp_coins + 1, 15)
                add_candidate(bot_coins, 10)        # occasional all-in
            else:
                # offset == 0 => pos=3 => center
                # Very balanced scenario => distribute bets around small, medium, bigger
                add_candidate(0, 15)
                add_candidate(3, 20)
                add_candidate(6, 25)
                add_candidate(10, 20)
                add_candidate(opp_coins + 1, 10)
                add_candidate(bot_coins, 10)

    # --------------------------------------------------
    # Now we have a candidate list of (bet, weight).
    # Pick a bet based on weighted random selection.
    # --------------------------------------------------
    if not candidates:
        # Fallback if something went wrong, at least bet 0
        return 0

    total_weight = sum(weight for (_, weight) in candidates)
    rand_choice = random.uniform(0, total_weight)
    running_sum = 0

    for (bet_value, weight) in candidates:
        running_sum += weight
        if rand_choice <= running_sum:
            return bet_value

    # Fallback
    return candidates[-1][0]