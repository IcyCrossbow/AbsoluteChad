#-------------------#
#      IMPORTS      #
#-------------------#

import discord
from discord import app_commands
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
    try:
        synced = await bot.tree.sync()
        print(f"🔧 Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

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
@bot.tree.command(name="announcement", description="Send an announcement embed")
@app_commands.describe(
    channel="The channel to send the announcement to",
    title="The title of the announcement",
    description="The main body text",
    fields="Optional fields in the format: Name1 | Value1 | Name2 | Value2 ...",
    image_url="Optional image URL to display in the embed",
    thumbnail_url="Optional thumbnail URL to display in the embed"
)
async def announcement(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str,
    description: str,
    fields: str = None,
    image_url: str = None,
    thumbnail_url: str = None
):
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())

    # Parse optional fields
    if fields:
        parts = [p.strip() for p in fields.split("|")]
        for i in range(0, len(parts), 2):
            if i+1 < len(parts):
                embed.add_field(name=parts[i], value=parts[i+1], inline=False)

    # Optional image and thumbnail
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    embed.set_footer(text=f"Sent by {interaction.user.display_name}")

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ Announcement sent to {channel.mention}", ephemeral=True)


bot.run(os.getenv("DISCORD_TOKEN"))
