import os
from discord.ext import commands, tasks
import discord
import random
import requests
import asyncio
import logging

class MilestoneBot:
    def __init__(self, token: str, place_id: str | int):
        self.token = token
        self.place_id = str(place_id)

        intents = discord.Intents.none()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True

        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.target_channel: discord.TextChannel | None = None
        self.is_running = False
        self.current_visits = 0
        self.milestone_goal = 3358

        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
        logging.getLogger("discord").setLevel(logging.WARNING)

        self.bot.add_listener(self.on_ready)
        self.setup_commands()

        self.milestone_loop = tasks.loop(seconds=65)(self._milestone_loop_body)

        self._http = requests.Session()
        self._http.headers.update({"User-Agent": "Mozilla/5.0 (MilestoneBot)"})

    async def on_ready(self):
        logging.info(f'Bot logged in as {self.bot.user}')
        try:
            await self.bot.change_presence(activity=discord.Game(name="Tracking visits…"))
        except Exception:
            pass

    # keep your commands and game-data methods here...
    # (I won’t rewrite them all — just remove Flask references)

    def run(self):
        self.bot.run(self.token)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    place_id = "125760703264498"  # your Roblox place ID
    if not token:
        print("Error: DISCORD_TOKEN not found")
        raise SystemExit(1)
    MilestoneBot(token, place_id).run()
