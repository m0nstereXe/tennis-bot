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

@bot.event
async def on_ready():
    synced_commands = await bot.tree.sync()
    print(f"Synced {len(synced_commands)} command(s).")
    print(f"Logged in as {bot.user}")

@bot.hybrid_command()
async def start(ctx):
    """
    Starts a new tennis game where the user is Player1 and the bot is Player2.
    """
    user_id = ctx.author.id
    if user_id in ongoing_games:
        await ctx.send(f"{ctx.author.mention}, you already have a game in progress!")
        return

    game = TennisGame(player1_id=ctx.author.id, player2_id=bot.user.id)
    ongoing_games[user_id] = game

    if randint(0,2)==0:
        await ctx.send("Why are you not doing spring contest?")

    await ctx.send(
        f"Game started! {ctx.author.mention} (Player1) vs {bot.user.mention} (Player2)\n"
    )

    state_display = generate_game_display(game)
    await ctx.send(state_display)


@bot.hybrid_command()
async def play(ctx, x: int):
    user_id = ctx.author.id
    if user_id not in ongoing_games:
        await ctx.send(f"{ctx.author.mention}, you have no active game. Use `!start` first.")
        return

    game = ongoing_games[user_id]

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

@bot.hybrid_command()
async def stop_game(ctx):
    """
    Command to stop your own game if needed.
    """
    user_id = ctx.author.id
    if user_id in ongoing_games:
        ongoing_games.pop(user_id)
        await ctx.send(f"{ctx.author.mention}, your game has been stopped.")
    else:
        await ctx.send(f"{ctx.author.mention}, you have no game in progress to stop.")

@bot.hybrid_command(name="tennis_help")
async def help_command(ctx):
    """
    A command that shows usage instructions for your Tennis Bot.
    """
    help_text = (
        "**Tennis Bot Commands**\n"
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
