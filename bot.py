
from flask import Flask
from threading import Thread
import os

# === Keep-alive server ===
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()


# === Discord bot ===
import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime
import random
import re
import requests
from bs4 import BeautifulSoup
import json

class MilestoneBot:
    def __init__(self, token):
        self.bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
        self.token = token
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

            playing, visits = self.get_game_data()
            if visits > 0:
                self.current_visits = visits
                if visits >= self.milestone_goal:
                    add_amount = random.choice([100, 150])
                    self.milestone_goal = visits + add_amount
                    print(f"Milestone reached! New goal: {self.milestone_goal:,}")

            message = f"""--------------------------------------------------
👤🎮 Active players: {playing}
--------------------------------------------------
👥 Visits: {visits:,}
🎯 Next milestone: {visits:,}/{self.milestone_goal:,}
--------------------------------------------------"""

            await ctx.send(message)

            if not self.milestone_loop.is_running():
                self.milestone_loop.start()
            await ctx.send("milestone bot started - made by PAWINCEE-")

        @self.bot.command(name='stopms')
        async def stop_milestone(ctx):
            if not self.is_running:
                await ctx.send("Bot is not running!")
                return

            self.is_running = False
            if self.milestone_loop.is_running():
                self.milestone_loop.cancel()
            await ctx.send("milestone bot stopped.")

    def get_game_data(self):
        # (Keep all your existing get_game_data logic here; omitted for brevity in this snippet)
        return 15, 3258  # placeholder fallback

    @tasks.loop(seconds=65)
    async def milestone_loop(self):
        if not self.target_channel or not self.is_running:
            return
        playing, visits = self.get_game_data()
        if visits > 0:
            self.current_visits = visits
            if visits >= self.milestone_goal:
                add_amount = random.choice([100, 150])
                self.milestone_goal = visits + add_amount
        message = f"""--------------------------------------------------
👤🎮 Active players: {playing}
--------------------------------------------------
👥 Visits: {visits:,}
🎯 Next milestone: {visits:,}/{self.milestone_goal:,}
--------------------------------------------------"""
        await self.target_channel.send(message)

    def run(self):
        self.bot.run(self.token)
