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

#-------------------#
#      INTENTS      #
#-------------------#

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
#   VOICE EVENTS    #
#-------------------#

@bot.event
async def on_voice_state_update(member, before, after):
    # Only care about joins (after.channel is not None, before.channel is None or different)
    if after.channel and after.channel.name in ["General Voice 1", "General Voice 2"]:
        # Replace with your Discord user ID
        owner_id = 144907705134481409  

        # Fetch the user object for you
        owner = await bot.fetch_user(owner_id)

        # Send a DM
        try:
            await owner.send(f"🔔 {member.display_name} just joined {after.channel.name}")
        except Exception as e:
            print(f"Could not send DM: {e}")


#-------------------#
#      COMMANDS     #
#-------------------#

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

bot.run(os.getenv("DISCORD_TOKEN"))
