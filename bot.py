#-------------------#
#      IMPORTS      #
#-------------------#
import discord
from discord import app_commands
from discord.ext import commands
import os, sys, time, threading
import json
import sdnotify  # pip install sdnotify

#-------------------#
#  SYSTEMD NOTIFY   #
#-------------------#
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
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#-------------------#
#   TASK BACKLOG    #
#-------------------#

TASKS_FILE = "tasks.json"
BACKLOG_META_FILE = "backlog.json"
tasks = []
BACKLOG_CHANNEL_ID = 1423326253456424970  # replace with your backlog channel ID
backlog_message_id = None

def load_tasks():
    global tasks
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            try:
                tasks = json.load(f)
            except json.JSONDecodeError:
                tasks = []
    else:
        tasks = []

def save_tasks():
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def load_backlog_meta():
    global backlog_message_id
    if os.path.exists(BACKLOG_META_FILE):
        with open(BACKLOG_META_FILE, "r") as f:
            try:
                data = json.load(f)
                backlog_message_id = data.get("message_id")
            except json.JSONDecodeError:
                backlog_message_id = None

def save_backlog_meta():
    with open(BACKLOG_META_FILE, "w") as f:
        json.dump({"message_id": backlog_message_id}, f)

async def update_backlog_embed(bot):
    channel = bot.get_channel(BACKLOG_CHANNEL_ID)
    if not channel:
        return

    if tasks:
        task_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
    else:
        task_text = "✅ No tasks in the backlog!"

    embed = discord.Embed(title="📋 Backlog", description=task_text, color=discord.Color.orange())

    global backlog_message_id
    try:
        if backlog_message_id:
            try:
                msg = await channel.fetch_message(backlog_message_id)
                await msg.edit(embed=embed)
            except discord.NotFound:
                msg = await channel.send(embed=embed)
                backlog_message_id = msg.id
                save_backlog_meta()
        else:
            msg = await channel.send(embed=embed)
            backlog_message_id = msg.id
            save_backlog_meta()
    except Exception as e:
        print(f"Error updating backlog: {e}")

#-------------------#
#       EVENTS      #
#-------------------#
GUILD_ID = 672020413559078913  # replace with your server ID

@bot.event
async def on_ready():
    load_tasks()
    load_backlog_meta()
    print(f"✅ Logged in as {bot.user}")
    try:
        guild = discord.Object(id=GUILD_ID)
        synced = await bot.tree.sync(guild=guild)
        print(f"🔧 Synced {len(synced)} command(s) to guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

    await update_backlog_embed(bot)

@bot.event
async def on_voice_state_update(member, before, after):
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

# SYNC
@bot.command()
async def sync(ctx):
    synced = await bot.tree.sync()
    await ctx.send(f"Synced {len(synced)} global command(s).")

# ANNOUNCEMENT
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
    # Acknowledge immediately to avoid timeouts
    await interaction.response.defer(ephemeral=True)

    # Basic permission guard: can the bot send to that channel?
    perms = channel.permissions_for(channel.guild.me)
    if not perms.send_messages:
        await interaction.followup.send("❌ I don't have permission to send messages in that channel.", ephemeral=True)
        return

    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())

    # Parse optional fields
    if fields:
        parts = [p.strip() for p in fields.split("|")]
        for i in range(0, len(parts), 2):
            if i + 1 < len(parts):
                embed.add_field(name=parts[i], value=parts[i+1], inline=False)

    # Optional image and thumbnail
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    embed.set_footer(text=f"Sent by {interaction.user.display_name}")

    try:
        await channel.send(embed=embed)
        await interaction.followup.send(f"✅ Announcement sent to {channel.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"⚠️ Failed to send announcement: {e}", ephemeral=True)

# GUIDE
@bot.tree.command(name="guide", description="Create a structured guide embed")
@app_commands.describe(
    channel="The channel to send the guide to",
    title="The title of the guide",
    intro="A short introduction or summary",
    steps="Steps separated by | (e.g. Step 1 | Step 2 | Step 3)",
    tips="Optional tips separated by | (e.g. Tip 1 | Tip 2)",
    image_url="Optional image URL to display at the bottom",
    thumbnail_url="Optional thumbnail URL to display in the corner"
)
async def guide(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str,
    intro: str,
    steps: str,
    tips: str = None,
    image_url: str = None,
    thumbnail_url: str = None
):
    # Acknowledge immediately
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(
        title=f"📘 {title}",
        description=f"{intro}\n\n──────────────────────────────",
        color=discord.Color.green()
    )

    # Parse steps into a numbered list
    step_list = [s.strip() for s in steps.split("|") if s.strip()]
    step_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(step_list)])
    embed.add_field(name="📝 Steps", value=step_text, inline=False)

    # Optional tips
    if tips:
        tip_list = [t.strip() for t in tips.split("|") if t.strip()]
        tip_text = "\n".join([f"• {t}" for t in tip_list])
        embed.add_field(name="💡 Tips", value=tip_text, inline=False)

    # Optional visuals
    if image_url:
        embed.set_image(url=image_url)
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    embed.set_footer(text=f"Guide created by {interaction.user.display_name}")

    # Send to chosen channel
    await channel.send(embed=embed)
    await interaction.followup.send(f"✅ Guide sent to {channel.mention}", ephemeral=True)


# TODO
@bot.tree.command(name="todo", description="Manage the backlog")
@app_commands.describe(action="add, list, or done", content="Task text or task number")
async def todo(interaction: discord.Interaction, action: str, content: str = None):
    await interaction.response.defer(ephemeral=True)

    if action.lower() == "add" and content:
        tasks.append(content)
        save_tasks()
        await interaction.followup.send(f"➕ Added task: {content}", ephemeral=True)

    elif action.lower() == "list":
        if tasks:
            task_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])
            await interaction.followup.send(f"📋 Current tasks:\n{task_text}", ephemeral=True)
        else:
            await interaction.followup.send("✅ No tasks in the backlog!", ephemeral=True)

    elif action.lower() == "done" and content:
        try:
            index = int(content) - 1
            removed = tasks.pop(index)
            save_tasks()
            await interaction.followup.send(f"✔️ Completed task: {removed}", ephemeral=True)
        except (ValueError, IndexError):
            await interaction.followup.send("⚠️ Invalid task number.", ephemeral=True)
    else:
        await interaction.followup.send("Usage: /todo add <task>, /todo list, /todo done <number>", ephemeral=True)

    await update_backlog_embed(bot)

#-------------------#
#   DISCORD_TOKEN   #
#-------------------#

bot.run(os.getenv("DISCORD_TOKEN"))