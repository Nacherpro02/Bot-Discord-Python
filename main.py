import os 
import discord
from discord.ext import commands
from discord import app_commands
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True

GUILD_ID = discord.Object(id=1253038375955464203)

client = commands.Bot(command_prefix='/', intents=intents)

@client.tree.command(name="ping", description="Replies with Pong!", guild=GUILD_ID)
async def ping(ctx: discord.Interaction):
    await ctx.response.send_message(f'Pong! {round(client.latency * 1000)}ms')

@client.tree.command(name="suma", description="Suma dos números", guild=GUILD_ID)
async def suma(ctx: discord.Interaction, num1: int, num2: int):
    await ctx.response.send_message(f'{num1 + num2}')


@client.command()
async def ping(ctx):
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')

@client.command()
async def suma(ctx: discord.Interaction, num1: int, num2: int):
    await ctx.send(f'{num1 + num2}')

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('!help'))
    print(f'{client.user} has connected to Discord!')
    try:
  
        await client.tree.sync(guild=GUILD_ID)
        print("Comandos de aplicación sincronizados con el servidor.")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")

    print(f'{client.user} se ha conectado a Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!Hello"):
        await message.channel.send(f"Hello {message.author}!")


    await client.process_commands(message)
client.run(TOKEN)