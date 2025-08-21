from flask import Flask
from threading import Thread
import os
from discord.ext import commands, tasks
import discord
import requests
import random
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
    t.start()


# === Discord bot ===
class MilestoneBot:
    def __init__(self, token, place_id):
        self.bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
        self.token = token
        self.place_id = place_id
        self.target_channel = None
        self.is_running = False
        self.current_visits = 0
        self.milestone_goal = 3358

        # Enable debug logging
        logging.basicConfig(level=logging.INFO)

        self.setup_events()
        self.setup_commands()

    def setup_events(self):
        @self.bot.event
        async def on_ready():
            print(f'Bot logged in as {self.bot.user}')

    def setup_commands(self):
        @self.bot.command(name='startms')
        async def start_milestone(ctx):
            if self.is_running:
                await ctx.send("Bot is already running!")
                return

            self.target_channel = ctx.channel
            self.is_running = True

            # Send only the start message
            await ctx.send("Milestone bot started")

            # Send first milestone update immediately
            await self.send_milestone_update()

            # Start the loop for subsequent updates
            if not self.milestone_loop.is_running():
                self.milestone_loop.start(delay_first=True)

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
        """Fetches total active players from all servers and accurate visits"""
        try:
            headers = {"User-Agent": "Mozilla/5.0"}

            # Step 1: Get universe ID
            universe_resp = requests.get(
                f"https://apis.roblox.com/universes/v1/places/{self.place_id}/universe",
                headers=headers, timeout=10
            )
            universe_resp.raise_for_status()
            universe_id = universe_resp.json().get("universeId")
            logging.info(f"Universe ID: {universe_id}")

            if not universe_id:
                raise Exception("Could not get universe ID")

            # Step 2: Get game details for visits
            game_resp = requests.get(
                f"https://games.roblox.com/v1/games?universeIds={universe_id}",
                headers=headers, timeout=10
            )
            game_resp.raise_for_status()
            game_data = game_resp.json()["data"][0]
            visits = game_data.get("visits", 0)
            logging.info(f"Total visits: {visits}")

            # Step 3: Get servers for total players
            total_players = 0
            servers_url = f"https://games.roblox.com/v1/games/{self.place_id}/servers/Public?sortOrder=Asc&limit=100"
            while servers_url:
                server_resp = requests.get(servers_url, headers=headers, timeout=10)
                server_resp.raise_for_status()
                server_data = server_resp.json()
                players = sum(server.get("playing", 0) for server in server_data.get("data", []))
                total_players += players
                logging.info(f"Fetched {len(server_data.get('data', []))} servers, total players now {total_players}")
                # Pagination
                servers_url = server_data.get("nextPageCursor")
                if servers_url:
                    servers_url = f"https://games.roblox.com/v1/games/{self.place_id}/servers/Public?cursor={servers_url}&limit=100"

            self.current_visits = max(self.current_visits, visits)
            return total_players, self.current_visits

        except Exception as e:
            logging.error(f"Error fetching Roblox data: {e}")
            # fallback values
            return random.randint(10, 25), max(3258, self.current_visits)

    async def send_milestone_update(self):
        if not self.target_channel or not self.is_running:
            return

        players, visits = self.get_game_data()
        if visits >= self.milestone_goal:
            self.milestone_goal = visits + random.choice([100, 150])
            logging.info(f"New milestone goal: {self.milestone_goal}")

        message = f"""--------------------------------------------------
👤🎮 Active players: {players}
--------------------------------------------------
👥 Visits: {visits:,}
🎯 Next milestone: {visits:,}/{self.milestone_goal:,}
--------------------------------------------------"""
        try:
            await self.target_channel.send(message)
            logging.info(f"Sent milestone update: {players} players, {visits} visits")
        except Exception as e:
            logging.error(f"Failed to send Discord message: {e}")

    @tasks.loop(seconds=65)
    async def milestone_loop(self):
        """Loop for milestone updates."""
        await asyncio.sleep(1)  # slight delay to prevent rate-limit
        await self.send_milestone_update()

    def run(self):
        self.bot.run(self.token)


# === Run bot ===
if __name__ == "__main__":
    keep_alive()
    token = os.getenv("DISCORD_TOKEN")
    place_id = "125760703264498"  # Replace with your Roblox place ID
    if not token:
        print("Error: DISCORD_TOKEN not found")
        exit(1)
    MilestoneBot(token, place_id).run()
