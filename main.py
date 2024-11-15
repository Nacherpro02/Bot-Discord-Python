import os
import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True
intents.voice_states = True

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
        if len(song_queue) > 1:
            song_queue.insert(0, song_queue.pop(1))
 
            await play_music(song_queue[0]['url'])
   

    @discord.ui.button(label="Adelante", style=discord.ButtonStyle.green)
    async def adelante(self, button: discord.ui.Button, interaction: discord.Interaction):
        contador = 0
        if len(song_queue) > 1:
            contador += 1
            await play_music(song_queue.pop(contador)['url'])


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
                await ctx.followup.send(f"Me he movido al canal {voice_channel.name}.")
            else:
                await ctx.followup.send(f"Ya estoy en el canal {voice_channel.name}.")
        else:
            voice_client = await voice_channel.connect()
            await ctx.followup.send(f"Conectado al canal {voice_channel.name}")

        song_queue.append({'url': url, 'title': url})  # Agregar canción a la cola

        if len(song_queue) == 1:
            await play_music(url)  # Si es la primera canción, la reproduce inmediatamente

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
            os.remove(current_song)  # Eliminar el archivo de música cuando se detiene
        await ctx.response.send_message("Reproducción detenida y archivo eliminado.")


@client.event
async def on_voice_state_update(member, before, after):
    global voice_client, current_song

    if before.channel is not None and member == client.user:
        if len(before.channel.members) == 1:  # Si el bot está solo en el canal
            voice_client = discord.utils.get(client.voice_clients, guild=member.guild)
            if voice_client and voice_client.is_connected():
                await voice_client.disconnect()
                if current_song and os.path.exists(current_song):
                    os.remove(current_song)  # Eliminar el archivo de música
                print("Bot desconectado por inactividad y archivo de música eliminado.")


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('/help'))
    print(f'{client.user} has connected to Discord!')
    try:
        await client.tree.sync()
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
