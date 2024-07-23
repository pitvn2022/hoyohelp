import platform
import psutil
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from utility import config, LOG

def format_timedelta(td):
    """Format a timedelta object into a string with days, hours, minutes, and seconds, showing only non-zero units."""
    seconds = int(td.total_seconds())
    days, remainder = divmod(seconds, 86400)  # 86400 seconds in a day
    hours, remainder = divmod(remainder, 3600)  # 3600 seconds in an hour
    minutes, seconds = divmod(remainder, 60)  # 60 seconds in a minute
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:  # Always show seconds if no other units are present
        parts.append(f"{seconds}s")

    return ' '.join(parts)

def format_memory(used, total):
    """Format memory usage to show in MiB or GiB based on the total memory."""
    if total >= 1024:  # If total memory is 1 GiB or more
        used_str = f"{used / 1024:.1f}GiB"
        total_str = f"{total / 1024:.1f}GiB"
    else:  # If total memory is less than 1 GiB
        used_str = f"{used:.1f}MiB"
        total_str = f"{total:.1f}MiB"
    
    return f"{used_str} / {total_str}"

# Custom owner check
def is_owner():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == config.owner_id
    return app_commands.check(predicate)

class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.utcnow()  # Track when the bot started

    @app_commands.command(name="stats", description="Show bot and system stats")
    @is_owner()
    async def slash_stats(self, interaction: discord.Interaction):
        # Log the command usage with user ID
        LOG.Cmd(f"@{interaction.user.name}#{interaction.user.id} used /stats：")

        # Get bot information
        bot_name = f"{self.bot.user.name}#{self.bot.user.discriminator}"
        bot_id = self.bot.user.id
        latency = round(self.bot.latency * 1000)
        uptime = format_timedelta(datetime.utcnow() - self.start_time)  # Bot's uptime

        # Get system information
        os_name = platform.system()
        os_version = platform.release()
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        memory_used = memory_info.used / (1024 ** 2)  # Convert to MiB
        memory_total = memory_info.total / (1024 ** 2)  # Convert to MiB
        memory_percentage = memory_info.percent

        memory_usage = format_memory(memory_used, memory_total)

        system_uptime_seconds = (datetime.utcnow() - datetime.fromtimestamp(psutil.boot_time())).total_seconds()
        system_uptime = format_timedelta(timedelta(seconds=system_uptime_seconds))  # System's uptime

        embed = discord.Embed(title=f"{bot_name} Info", color=discord.Color.blue())
        embed.add_field(name="Name", value=f"{bot_name}", inline=False)
        embed.add_field(name="API Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="Bot Uptime", value=uptime, inline=True)
        embed.add_field(name="Guilds", value=f"{len(self.bot.guilds)}", inline=True)

        embed.add_field(name="System Stats", value=f"OS: {os_name} {os_version}", inline=False)
        embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="Memory Usage", value=f"{memory_usage}", inline=True)
        embed.add_field(name="Memory Usage Percentage", value=f"{memory_percentage}%", inline=True)
        embed.add_field(name="System Uptime", value=system_uptime, inline=True)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Stats(bot))
