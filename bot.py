from flask import Flask
from threading import Thread
import os
from discord.ext import commands, tasks
import discord
import random
import requests
import asyncio
import logging

# === Keep-alive server ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    print("Flask server starting...")
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True  # ensures it doesn't block exit
    t.start()

# === Discord Bot ===
class MilestoneBot:
    def __init__(self, token, place_id):
        self.token = token
        self.place_id = place_id
        self.bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
        self.target_channel = None
        self.is_running = False
        self.current_visits = 0
        self.milestone_goal = 3358

        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

        self.bot.add_listener(self.on_ready)
        self.setup_commands()
        self.milestone_loop = tasks.loop(seconds=65)(self._milestone_loop_body)

    async def on_ready(self):
        logging.info(f'Bot logged in as {self.bot.user}')

    def setup_commands(self):
        @self.bot.command(name='startms')
        async def start_milestone(ctx):
            if self.is_running:
                await ctx.send("Bot is already running!")
                return

            self.target_channel = ctx.channel
            self.is_running = True

            await ctx.send("Milestone bot started")
            await self.send_milestone_update()  # first update immediately

            if not self.milestone_loop.is_running():
                self.milestone_loop.start()  # subsequent updates every 65s

        @self.bot.command(name='stopms')
        async def stop_milestone(ctx):
            if not self.is_running:
                await ctx.send("Bot is not running!")
                return
            self.is_running = False
            if self.milestone_loop.is_running():
                self.milestone_loop.cancel()
            await ctx.send("Milestone bot stopped")

    def get_game_data(self):
        """Fetch total players and total visits safely with fallbacks."""
        headers = {"User-Agent": "Mozilla/5.0"}
        total_players = 0
        visits = self.current_visits

        try:
            # Universe ID
            universe_resp = requests.get(
                f"https://apis.roblox.com/universes/v1/places/{self.place_id}/universe",
                headers=headers, timeout=10
            )
            universe_resp.raise_for_status()
            universe_id = universe_resp.json().get("universeId")
            if not universe_id:
                raise Exception("Cannot get universe ID")

            # Visits
            game_resp = requests.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}",
                headers=headers, timeout=10
            )
            game_resp.raise_for_status()
            api_visits = game_resp.json()["data"][0].get("visits", None)
            if api_visits is not None and api_visits > 0:
                visits = api_visits
            self.current_visits = max(self.current_visits, visits)

            # Active players across all public servers
            cursor = ""
            while True:
                servers_url = f"https://games.roblox.com/v1/games/{self.place_id}/servers/Public?sortOrder=Asc&limit=100"
                if cursor:
                    servers_url += f"&cursor={cursor}"
                server_resp = requests.get(servers_url, headers=headers, timeout=10)
                server_resp.raise_for_status()
                server_data = server_resp.json()
                data_list = server_data.get("data", [])
                total_players += sum(s.get("playing", 0) for s in data_list)
                cursor = server_data.get("nextPageCursor")
                if not cursor:
                    break

            return total_players, self.current_visits

        except Exception as e:
            logging.error(f"Error fetching game data: {e}")
            return random.randint(10, 25), max(3258, self.current_visits)

    async def send_milestone_update(self):
        if not self.target_channel or not self.is_running:
            return
        players, visits = self.get_game_data()
        if visits >= self.milestone_goal:
            self.milestone_goal = visits + random.choice([100, 150])
        message = f"""--------------------------------------------------
👤🎮 Active players: {players}
--------------------------------------------------
👥 Visits: {visits:,}
🎯 Next milestone: {visits:,}/{self.milestone_goal:,}
--------------------------------------------------"""
        try:
            await asyncio.sleep(1)
            await self.target_channel.send(message)
        except Exception as e:
            logging.error(f"Failed to send Discord message: {e}")

    async def _milestone_loop_body(self):
        await self.send_milestone_update()

    def run(self):
        self.bot.run(self.token)

# === Run bot ===
if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    place_id = "125760703264498"  # your Roblox place ID
    if not token:
        print("Error: DISCORD_TOKEN not found")
        exit(1)
    MilestoneBot(token, place_id).run()
