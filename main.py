import os
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
from dotenv import load_dotenv
import aiohttp
import random

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.voice_states = True
channel_id = 1311745347848110091 
url = "https://www.vicinityclo.de/products/akimbo-lows-pristina-moss"

GUILD_ID = discord.Object(id=os.getenv('GUILD_ID'))

client = commands.Bot(command_prefix='/', intents=intents)

ydl_opts = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'outtmpl': 'downloads/%(id)s.%(ext)s',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3', 
        'preferredquality': '192', 
    }],
}

song_queue = []
current_song = None
voice_client = None
contador = 0

class MusicControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Volver", style=discord.ButtonStyle.green)
    async def volver(self, button: discord.ui.Button, interaction: discord.Interaction):
        global contador
        if len(song_queue) > 1:
            contador -= 1
            await play_music(song_queue[contador])
   

    @discord.ui.button(label="Adelante", style=discord.ButtonStyle.green)
    async def adelante(self, button: discord.ui.Button, interaction: discord.Interaction):
        contador = 0
        if len(song_queue) > 1:
            contador += 1
            await play_music(song_queue[contador])


    @discord.ui.button(label="Pausar", style=discord.ButtonStyle.red)
    async def pausar(self, button: discord.ui.Button, interaction: discord.Interaction):
        if voice_client.is_playing():
            voice_client.pause()


    @discord.ui.button(label="Continuar", style=discord.ButtonStyle.green)
    async def continuar(self, button: discord.ui.Button, interaction: discord.Interaction):
        if voice_client.is_paused():
            voice_client.resume()




async def play_music(url):
    global current_song, voice_client, contador

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = f"downloads/{info['id']}.mp3"
        title = info.get('title', 'audio desconocido')

    if os.path.exists(file_path):
        print(f"Archivo descargado: {file_path}")
        voice_client.play(
            discord.FFmpegPCMAudio(file_path),
            after=lambda e: print(f"Error en la reproducción: {e}") if e else None
        )
        current_song = file_path

    await client.get_channel(voice_client.channel.id).send(f"Reproduciendo: {title}")


@client.tree.command(name="ping", description="Comando de prueba")
async def ping(ctx: discord.Interaction):
    await ctx.response.send_message(f"Pong! {round(client.latency * 1000)}ms")
    print("Comando ping ejecutado.")


@client.tree.command(name="musica", description="Reproducir música")
async def musica(ctx: discord.Interaction, url: str):
    global voice_client, song_queue

    await ctx.response.defer()
    if ctx.user.voice:
        voice_channel = ctx.user.voice.channel

        if ctx.guild.voice_client:
            voice_client = ctx.guild.voice_client
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()
            await ctx.followup.send(f"Conectado al canal {voice_channel.name}")

        song_queue.append({'url': url, 'title': url})

        if len(song_queue) >= 1:
            await play_music(url)

        await ctx.followup.send(f"Agregado a la cola: {url}")
        view = MusicControls()
        await ctx.followup.send("Controles de música:", view=view)

    else:
        await ctx.followup.send("Debes estar en un canal de voz primero.")
        return


@client.tree.command(name="stop", description="Detener la reproducción")
async def stop(ctx: discord.Interaction):
    global voice_client, current_song

    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        if current_song and os.path.exists(current_song):
            os.remove(current_song)
        await ctx.response.send_message("Reproducción detenida, saliendo...")


def get_random_time():
    """Genera un número aleatorio entre 30 y 60 segundos."""
    return random.randint(30, 60)

# Función de verificación HTTP

async def check_http_and_notify():
    print("Verificando la URL...")  # Verificamos si esta línea se imprime
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                status = response.status
                print(f"Estado HTTP: {status}")  # Depuración adicional para ver el estado
        return status
    except Exception as e:
        print(f"Error al verificar la URL: {e}")

# Bucle que ejecuta la función de manera continua
@client.command()
async def req(ctx):
    await ctx.send("Comando ejecutando...")
    print("Iniciando el bucle principal...")  # Depuración para ver si entra en el bucle
    while True:
        try:
            status = await check_http_and_notify()
            if status == 200:
                print("Código 200 encontrado, enviando mensaje a Discord.")
                await ctx.send("¡La URL ha respondido con un código 200!")
            else:
                print(f"Respuesta HTTP: {status}. No se envió mensaje.")
                await ctx.send(f"¡La URL no está disponible, código {status}!")              # Llamar a la función que hace la solicitud HTTP
        except Exception as e:
            print(f"Error al verificar la URL: {e}")
        
        # Espera aleatoria entre 30 y 60 segundos antes de hacer otra solicitud
        await asyncio.sleep(get_random_time())


@client.tree.command(name="hola", description="Comando de prueba")
async def hola(ctx: discord.Interaction):
    await ctx.response.send_message('¡Hola! ¿Cómo estás?')

@client.event
async def on_voice_state_update(member, before, after):
    global voice_client, current_song

    if before.channel is not None and member == client.user:
        if len(before.channel.members) == 1: 
            voice_client = discord.utils.get(client.voice_clients, guild=member.guild)
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                song_queue = []
                os.remove("downloads/")
                print("Bot desconectado por inactividad y archivo de música eliminado.")


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('/help'))
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
    await client.process_commands(message)

client.run(TOKEN)
