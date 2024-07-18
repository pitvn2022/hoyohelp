# cogs_external/server.py

import discord
from discord.ext import commands, tasks
from aiohttp import web
import time
import logging

from utility import LOG  # Import your logging utility

class Server(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.web_app = web.Application()
        self.web_app.router.add_get('/', self.handle_root)
        self.runner = web.AppRunner(self.web_app)
        self.web_server.start()

        # Suppress aiohttp access logs
        logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

    @tasks.loop(count=1)
    async def web_server(self):
        await self.runner.setup()
        site = web.TCPSite(self.runner, 'localhost', 8080)
        await site.start()

    async def handle_root(self, request):
        uptime_seconds = int(time.time() - self.start_time)
        uptime_str = self.format_uptime(uptime_seconds)
        return web.Response(text=f"Uptime: {uptime_str}")

    def format_uptime(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    @commands.Cog.listener()
    async def on_ready(self):
        LOG.System("Web server running on http://localhost:8080")

    def cog_unload(self):
        self.web_server.cancel()

async def setup(bot):
    await bot.add_cog(Server(bot))
