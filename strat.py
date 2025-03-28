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