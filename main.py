#!/usr/bin/env python3
"""Simple Milestone Bot for Discord - tracks Roblox game statistics
Only sends 3 types of messages: start, stop, and milestone data
"""

import sys
import logging
from bot import MilestoneBot
import os
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Discord token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        sys.exit(1)
    
    # Start the bot
    try:
        bot = MilestoneBot(token)
        bot.run()
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
