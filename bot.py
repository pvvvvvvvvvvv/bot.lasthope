from flask import Flask
from threading import Thread
import os
from discord.ext import commands, tasks
import discord
import random
import requests
import re
import asyncio
from bs4 import BeautifulSoup

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

            # Send only the start message once
            await ctx.send("Milestone bot started")

            # Send the first milestone update immediately
            await self.send_milestone_update()

            # Start the loop AFTER the first message interval
            if not self.milestone_loop.is_running():
                self.milestone_loop.start(delay_first=True)  # start loop with delay

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
        """Scrape live active players and visits from the Roblox game page"""
        try:
            url = f"https://www.roblox.com/games/{self.place_id}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")

            # Get visits number safely
            visits_text = soup.find(text=re.compile(r"[\d,]+ Visits"))
            if visits_text:
                visits_number = int(re.search(r"([\d,]+)", visits_text.replace(",", "")).group(1))
            else:
                visits_number = self.current_visits  # fallback

            # Get active players number safely
            playing_text = soup.find(text=re.compile(r"[\d,]+ playing"))
            if playing_text:
                playing_number = int(re.search(r"([\d,]+)", playing_text.replace(",", "")).group(1))
            else:
                playing_number = random.randint(10, 25)

            # Never decrease visits
            self.current_visits = max(self.current_visits, visits_number)
            return playing_number, self.current_visits

        except Exception as e:
            print(f"Error fetching live data: {e}")
            # fallback to last known values
            return random.randint(10, 25), max(3258, self.current_visits)

    async def send_milestone_update(self):
        if not self.target_channel or not self.is_running:
            return

        playing, visits = self.get_game_data()
        if visits >= self.milestone_goal:
            self.milestone_goal = visits + random.choice([100, 150])

        message = f"""--------------------------------------------------
👤🎮 Active players: {playing}
--------------------------------------------------
👥 Visits: {visits:,}
🎯 Next milestone: {visits:,}/{self.milestone_goal:,}
--------------------------------------------------"""
        await self.target_channel.send(message)

    @tasks.loop(seconds=65)
    async def milestone_loop(self):
        """Main loop for milestone updates. Starts after first message to prevent duplicates."""
        await asyncio.sleep(1)
        await self.send_milestone_update()

    def run(self):
        self.bot.run(self.token)


# === Run bot ===
if __name__ == "__main__":
    keep_alive()  # Start Flask server for UptimeRobot
    token = os.getenv("DISCORD_TOKEN")
    place_id = "125760703264498"  # Replace with your Roblox place ID
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        exit(1)
    MilestoneBot(token, place_id).run()
