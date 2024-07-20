import asyncio
import os
import sys

import discord
from discord import app_commands
from discord.ext import commands

from utility import config, LOG

# Custom owner check
def is_owner():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.id == config.owner_id
    return app_commands.check(predicate)

class Restart(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="restart", description="Restart the bot")
    @is_owner()
    async def restart(self, interaction: discord.Interaction):
        await interaction.response.send_message("Restarting the bot...", ephemeral=True)
        LOG.System("Restart command received, restarting the bot...")

        await self.bot.close()
        os.execv(sys.executable, [sys.executable] + sys.argv)

async def setup(bot: commands.Bot):
    await bot.add_cog(Restart(bot))
