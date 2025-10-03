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
# Put your server (guild) ID here
GUILD_ID = 672020413559078913

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        # Clear global commands
        await bot.tree.sync()  # syncs the *current* tree globally
        await bot.tree.clear_commands(guild=None)  # clear global definitions
        await bot.tree.sync()  # push the cleared state globally
        
        guild = discord.Object(id=GUILD_ID)
        # Sync commands only to this guild
        synced = await bot.tree.sync(guild=guild)
        print(f"🔧 Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

#-------------------#
#   VOICE EVENTS    #
#-------------------#

#SEND DM WHEN JOINED VC1 / VC2
@bot.event
async def on_voice_state_update(member, before, after):
    # Only trigger when the member actually joins a channel (was None before, now in a channel)
    if before.channel is None and after.channel is not None:
        if after.channel.name in ["General Voice 1", "General Voice 2"]:
            owner_id = 144907705134481409  # your Discord user ID
            owner = await bot.fetch_user(owner_id)
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
    await interaction.response.defer(ephemeral=True)  # acknowledge right away
    
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
    await interaction.followup.send(f"✅ Announcement sent to {channel.mention}", ephemeral=True)


#EDIT EMBED MESSAGE
@bot.tree.command(name="edit_announcement", description="Edit an existing announcement embed")
async def edit_announcement(interaction: discord.Interaction,
                            channel: discord.TextChannel,
                            message_id: str,
                            new_title: str = None,
                            new_description: str = None):
    await interaction.response.defer(ephemeral=True)  # 👈 acknowledge immediately

    try:
        msg = await channel.fetch_message(int(message_id))

        if not msg.embeds:
            await interaction.followup.send("⚠️ That message has no embed to edit.", ephemeral=True)
            return

        embed = msg.embeds[0].copy()
        if new_title:
            embed.title = new_title
        if new_description:
            embed.description = new_description

        await msg.edit(embed=embed)
        await interaction.followup.send(f"✅ Embed updated in {channel.mention}", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"⚠️ Could not edit message: {e}", ephemeral=True)

bot.run(os.getenv("DISCORD_TOKEN"))
