#-------------------#
#      IMPORTS      #
#-------------------#

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

#LOGGED IN AS AT STARTUP
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

#-------------------#
#   VOICE EVENTS    #
#-------------------#

#SEND DM WHEN JOINED VC1 / VC2
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

#PING-PONG
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

#SEND EMBED MESSAGE
@bot.command(name="sendembed")
@commands.has_any_role(672021816008507402, 672022138063945729)  # 👈 put your role IDs here
async def send_embed(ctx, channel: discord.TextChannel, *, message: str):
    """
    Send an embed as the bot to a specific channel.
    Usage: !sendembed #channel Your message here
    """
    embed = discord.Embed(
        title="📢 Announcement",
        description=message,
        color=discord.Color.blue()  # you can change the color
    )
    # Add building blocks here
    #embed.add_field(name="Extra Info", value="Some details here", inline=False)
    embed.set_footer(text=f"Sent by {ctx.author.display_name}")

    try:
        await channel.send(embed=embed)
        await ctx.send(f"✅ Embed sent to {channel.mention}")
    except Exception as e:
        await ctx.send(f"⚠️ Could not send embed: {e}")


bot.run(os.getenv("DISCORD_TOKEN"))
