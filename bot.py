import discord
from random import randint
from discord.ext import commands

from dotenv import load_dotenv
load_dotenv()
import os

from game_logic import TennisGame, generate_game_display
from strat import bot_strategy, new_strat

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # needed to read user messages
bot = commands.Bot(command_prefix="!", intents=intents)

ongoing_games = {}

ongoing_requests = {}

def convert_mention_to_id(mention):
    return int(mention[1:][:len(mention)-2].replace("@","").replace("!",""))

@bot.event
async def on_ready():
    synced_commands = await bot.tree.sync()
    print(f"Synced {len(synced_commands)} command(s).")
    print(f"Logged in as {bot.user}")

@bot.hybrid_command()
async def challenge(ctx, opponent):
    user = ctx.author
    opponent = await bot.fetch_user(convert_mention_to_id(opponent))

    if user.id in ongoing_games:
        await ctx.send(f"{ctx.author.mention}, you already have a game in progress!")
        return
    elif opponent.id in ongoing_games:
        await ctx.send(f"{opponent.mention} already has a game in progress!")
        return
    
    requestmsg = await ctx.send(f"Waiting for {opponent.mention}'s response...")
    await requestmsg.add_reaction('✅')
    await requestmsg.add_reaction('❌')

    ongoing_requests[requestmsg.id] = ctx.author.id

@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.id in ongoing_requests:
        if(user.id == reaction.message.mentions[0].id):
            if(reaction.emoji == "✅"):
                player2_id = reaction.message.mentions[0].id
                player1_id = ongoing_requests[reaction.message.id]
                await startGame(reaction.message.channel, [player1_id, player2_id], botGame=False)
            elif(reaction.emoji == "❌"):
                del ongoing_requests[reaction.message.id]
                await reaction.message.channel.send(f"{reaction.message.mentions[0].mention} rejected your challenge!")


@bot.hybrid_command()
async def start(ctx):
    #starting a game with the bot
    if ctx.author.id in ongoing_games:
        await ctx.send(f"{ctx.author.mention}, you already have a game in progress!")
        return
    await ctx.send("Starting game with bot!")
    await startGame(ctx.channel, [ctx.author.id, bot.user.id], botGame=True)

async def startGame(channel, players, botGame):
    """
    Starts a new tennis game between a bot and user if botGame is true, otherwise between a user and a user.
    """
    player1_id = players[0]
    player2_id = players[1]


    game = TennisGame(player1_id=player1_id, player2_id=player2_id)
    ongoing_games[player1_id] = game
    if not botGame:
        ongoing_games[player2_id] = game
    
    if randint(0,2)==0:
        await channel.send("Why are you not doing spring contest?")

    player1 = await bot.fetch_user(player1_id)
    player2 = await bot.fetch_user(player2_id)

    await channel.send(
        f"Game started! {player1.mention} (Player1) vs {player2.mention} (Player2)\n"
    )

    state_display = generate_game_display(game)
    await channel.send(state_display)

@bot.hybrid_command()
async def play(ctx, x: int):
    user_id = ctx.author.id
    if user_id not in ongoing_games:
        await ctx.send(f"{ctx.author.mention}, you have no active game. Use `!start` first.")
        return

    game = ongoing_games[user_id]
    if(game.player2_id == bot.user.id):
        if ctx.author.id == game.player1_id:
            if x < 0 or x > game.a:
                await ctx.send(f"{ctx.author.mention}, invalid move! Choose between 0 and {game.a}.")
                return

            y = new_strat(game.b, game.a, game.p)
            game.play_round(x, y)

            await ctx.send(f"{ctx.author.mention} spent {x} coins.\n"
                        f"{bot.user.mention} (Bot) spent {y} coins.")

            state_display = generate_game_display(game)
            await ctx.send(state_display)

            if not game.active:
                result = game.check_winner()
                if result == "Player1":
                    await ctx.send(f"{ctx.author.mention} wins! 🏆")
                elif result == "Player2":
                    await ctx.send(f"{bot.user.mention} wins! 🏆")
                else:
                    await ctx.send("It’s a tie!")
                ongoing_games.pop(user_id, None)
    else:
        if(game.player1_id == ctx.author.id and not game.betsPlaced[0]):
            game.bets[0] = x
            game.betsPlaced[0] = True
            player1 = await bot.fetch_user(game.player1_id)
            await ctx.send(f"{player1.mention} placed their bet!")
        elif(game.player2_id == ctx.author.id and not game.betsPlaced[1]):
            game.bets[1] = x
            game.betsPlaced[1] = True
            player2 = await bot.fetch_user(game.player2_id)
            await ctx.send(f"{player2.mention} placed their bet!")

        if(game.betsPlaced[0] and game.betsPlaced[1]):
            game.betsPlaced[0] = False
            game.betsPlaced[1] = False
            player1 = await bot.fetch_user(game.player1_id)
            player2= await bot.fetch_user(game.player2_id)
            game.play_round(game.bets[0], game.bets[1])

            await ctx.send(f"{player1.mention} spent {game.bets[0]} coins.\n"
                        f"{player2.mention} spent {game.bets[1]} coins.")
            
            state_display = generate_game_display(game)

            await ctx.send(state_display)
            if not game.active:
                result = game.check_winner()
                if result == "Player1":
                    await ctx.send(f"{player1.mention} wins! 🏆")
                elif result == "Player2":
                    await ctx.send(f"{player2.mention} wins! 🏆")
                else:
                    await ctx.send("It’s a tie!")
                ongoing_games.pop(game.player1_id, None)
                ongoing_games.pop(game.player2_id, None)

@bot.hybrid_command()
async def stop_game(ctx):
    """
    Command to stop your own game if needed.
    """
    user_id = ctx.author.id
    if user_id in ongoing_games:
        usergame = ongoing_games[user_id]
        player1 = await bot.fetch(usergame.player1_id)
        player2 = await bot.fetch(usergame.player2_id)
        ongoing_games.pop(usergame.player1_id, None)
        await ctx.send(f"{player1.mention}, your game has been stopped.")
        if(usergame.player2_id != bot.user.id):
            ongoing_games.pop(usergame.player2_id, None)
            
            await ctx.send(f"{player2.mention}, your game has been stopped.")
    else:
        await ctx.send(f"{ctx.author.mention}, you have no game in progress to stop.")

@bot.hybrid_command(name="tennis_help")
async def help_command(ctx):
    """
    A command that shows usage instructions for your Tennis Bot.
    """
    help_text = (
        "**Tennis Bot Commands**\n"
        "`!challenge - Sends a game request to another user`"
        "`!start` — Start a new game (you vs the bot)\n"
        "`!play x` — Play a round by spending x coins (x must be <= your current coins)\n"
        "`!stop_game` — Stop your current game\n"
        "\n"
        "**Goal**: Move the ball off the opponent’s side to win or force a tie if it ends in the center.\n"
        "**Rules**:\n"
        "1. The ball starts in the middle of 5 cups.\n"
        "2. Each round, you choose how many coins to spend (0 ≤ x ≤ your_coins).\n"
        "3. Bot secretly does the same.\n"
        "4. Higher spender pushes the ball one cup to their advantage.\n"
        "5. Ties do not move the ball.\n"
        "6. Game ends if the ball falls off an edge or if both players run out of coins.\n"
    )
    await ctx.send(help_text)


bot.run(BOT_TOKEN)
