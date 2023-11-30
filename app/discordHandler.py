import os
import discord
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
client = discord.Client(intents=intents)


bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
async def set_channel(ctx, channel_id: int):
    global CHANNEL_ID
    CHANNEL_ID = channel_id
    await ctx.send(f'Channel set to {channel_id}')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    if 'CHANNEL_ID' in globals():
        channel = bot.get_channel(CHANNEL_ID)
        await channel.send("Hello World!")

bot.run(TOKEN)
