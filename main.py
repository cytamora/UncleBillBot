import discord
import os
import asyncio
import subprocess
import openai
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# whisper_url = 'whisper_1_url'
openai.api_key = "******"

@bot.command()
async def join(ctx):
    if ctx.author.voice is None:
        await ctx.send("You're not in a voice channel.")
        return
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send(f'Joined {channel}')

@bot.command()
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
        await ctx.send(f'Left {voice_client.channel}')

@bot.command()
async def boom(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_connected():
    # Play the "vine-boom.mp3" file from the local directory
        voice_client.play(discord.FFmpegPCMAudio("vine-boom.mp3"))
    elif not voice_client.is_connected():
        await ctx.send("I'm not connected to a voice channel.")
        return

@bot.command()
async def listen(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_playing():
        await ctx.send("Already recording!")
        return
    elif not voice_client.is_connected():
        await ctx.send("I'm not connected to a voice channel.")
        return
    await ctx.send("Recording started!")
    while True:
        # Start recording 5 seconds of audio
        filename = 'audio.wav'
        command = f"ffmpeg -hide_banner -loglevel error -t 5 -f lavfi -i anullsrc -f s16le -ar 48000 -ac 2 pipe:1 > {filename}"
        process = subprocess.Popen(command, shell=True)

        # Wait for 5 seconds
        await asyncio.sleep(5)

        # Stop recording and get the audio data
        process.kill()
        # with open(filename, 'rb') as f:
        #     audio_data = io.BytesIO(f.read())

        # Send audio to Whisper-1 for transcription
        # async with aiohttp.ClientSession() as session:
        #     async with session.post(whisper_url, data=audio_data) as resp:
        #         transcript = await resp.text()
        audio_file= open("audio.wav", "rb")
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
        # Check for the word "leave" in the transcript
        if "leave" in transcript.lower():
            await voice_client.disconnect()
            await ctx.send(f'Left {voice_client.channel}')
            break

        # Delete the audio file
        os.remove(filename)

    await ctx.send("Recording stopped!")

bot.run("*******")
