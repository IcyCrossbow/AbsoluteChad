import discord
from discord.ext import commands
import os, sys, time, threading
import sdnotify  # install with: pip install sdnotify

# Start systemd notifier
notifier = sdnotify.SystemdNotifier()

def watchdog_loop():
    while True:
        notifier.notify("WATCHDOG=1")  # heartbeat
        time.sleep(30)  # must be less than WatchdogSec

threading.Thread(target=watchdog_loop, daemon=True).start()

intents = discord.Intents.default()
intents.message_content = True  # needed for reading messages

bot = commands.Bot(command_prefix="!", intents=intents)

#-------------------#
#       EVENTS      #
#-------------------#

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

#-------------------#
#      COMMANDS     #
#-------------------#

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

bot.run(os.getenv("DISCORD_TOKEN"))
