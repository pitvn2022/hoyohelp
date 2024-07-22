import os
import subprocess
import sys
import time

import discord
from discord import app_commands
from discord.ext import commands

from utility import LOG, config  # Import LOG and config from utility

# Custom owner check
def is_owner():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == config.owner_id  # Check if user is the owner
    return app_commands.check(predicate)

class Update(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="update", description="Update the bot from the Git repository")
    @is_owner()
    async def update(self, interaction: discord.Interaction):
        await interaction.response.send_message("Checking for updates...", ephemeral=True)
        LOG.Cmd(f"@{interaction.user.name}#{interaction.user.discriminator} used /update")
        LOG.System("Update command received, checking for updates...")

        # Fetch the latest changes from the remote repository
        fetch_result = subprocess.run(["git", "fetch"], capture_output=True, text=True)
        if fetch_result.returncode != 0:
            await interaction.followup.send(f"Failed to fetch from Git: {fetch_result.stderr}")
            LOG.System(f"Failed to fetch from Git: {fetch_result.stderr}")
            return

        # Check for differences between local and remote versions
        local_version = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        remote_version = subprocess.run(["git", "rev-parse", "@{u}"], capture_output=True, text=True).stdout.strip()

        if local_version == remote_version:
            await interaction.followup.send("The bot is already up-to-date.")
            LOG.System("The bot is already up-to-date.")
            return

        # Pull the latest changes from the Git repository
        pull_result = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if pull_result.returncode != 0:
            await interaction.followup.send(f"Failed to pull from Git: {pull_result.stderr}")
            LOG.System(f"Failed to pull from Git: {pull_result.stderr}")
            return

        await interaction.followup.send("Successfully updated the bot. Restarting now...")
        LOG.System("Successfully updated the bot. Restarting now...")

        # Wait a few seconds to ensure the update message is sent
        time.sleep(5)

        # Restart the bot
        os.execv(sys.executable, ['python'] + sys.argv)

async def setup(bot: commands.Bot):
    await bot.add_cog(Update(bot))
