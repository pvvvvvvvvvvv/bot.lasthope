from flask import Flask
from threading import Thread
import os
from discord.ext import commands, tasks
import discord
import random
import asyncio

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
    def __init__(self, token):
        self.bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
        self.token = token
        self.target_channel = None
        self.is_running = False
        self.current_visits = 3258  # starting visits
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

            # Send only the start message
            await ctx.send("Milestone bot started")

            # Start the loop (first milestone update comes after interval)
            if not self.milestone_loop.is_running():
                self.milestone_loop.start()

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
        # TODO: Replace with your real Roblox fetching logic
        # Currently simulates realistic updates
        variation = random.randint(-5, 8)
        playing = max(1, 15 + variation)
        self.current_visits += random.randint(0, 3)
        return playing, self.current_visits

    @tasks.loop(seconds=65)
    async def milestone_loop(self):
        if not self.target_channel or not self.is_running:
            return
        await asyncio.sleep(1)  # slight delay to reduce 429 risk
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

    def run(self):
        self.bot.run(self.token)


# === Run bot ===
if __name__ == "__main__":
    keep_alive()  # Start Flask server for UptimeRobot
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables!")
        exit(1)
    MilestoneBot(token).run()
