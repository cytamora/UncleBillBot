import asyncio
import os
import wave
import io

import whisper
import discord
import openai
from discord.ext import commands
from dotenv import load_dotenv
from profanity_check import predict

# Load the .env file
load_dotenv()

# Configure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_TOKEN")
model = whisper.load_model(
    name="base.en",
    # device="cpu",
)

# Initialize Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(
    description="Relatively simple music bot example",
    intents=intents,
)

connections = {}


async def finished_callback(sink, channel: discord.TextChannel, *args):
    # recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    await sink.vc.disconnect()
    for user_id in sink.audio_data.keys():
        os.remove(f"/tmp/{user_id}.wav")


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.slash_command(
    description="Sends the bot's latency."
)  # this decorator makes a slash command
async def ping(ctx):  # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")


@bot.slash_command(name="record", description="Record audio")
async def start(ctx):
    voice = ctx.author.voice

    if not voice:
        return await ctx.send("You're not in a vc right now")

    vc = await voice.channel.connect()
    connections.update({ctx.guild.id: vc})
    sink = discord.sinks.WaveSink()
    vc.start_recording(
        sink,
        finished_callback,
        ctx.channel,
    )

    await asyncio.sleep(1)
    await ctx.respond("The recording has started!")

    while vc.recording:
        await asyncio.sleep(0.1)
        user_data_copy = sink.audio_data.copy()
        for user, audio_stream in user_data_copy.items():
            # Seek to start of file
            audio_stream.file.seek(0)

            # Copy file to new BytesIO object and truncate the recording file
            audio_file_copy = io.BytesIO(audio_stream.file.read())

            # Calculate the number of seconds of audio given the file size and sample rate and truncate the file if it's too long
            if (
                audio_file_copy.getbuffer().nbytes
                / (vc.decoder.SAMPLING_RATE * vc.decoder.SAMPLE_SIZE)
                > 3.0
            ):
                audio_stream.file.truncate(0)

            # Encode the copied file to WAV
            with wave.open(audio_file_copy, "wb") as f:
                f.setnchannels(vc.decoder.CHANNELS)
                f.setsampwidth(vc.decoder.SAMPLE_SIZE // vc.decoder.CHANNELS)
                f.setframerate(vc.decoder.SAMPLING_RATE)

            # Seek to beginning of file
            audio_file_copy.seek(0)

            with open(f"/tmp/{user}.wav", "wb") as f:
                f.write(audio_file_copy.getbuffer())

            result = model.transcribe(audio=f"/tmp/{user}.wav", language="en")
            # print(f'[{user}] -> {result["text"]} [took {time.time() - start_time}s]')

            if predict([result["text"]])[0] == 1:
                audio_stream.file.truncate(0)
                source = discord.FFmpegPCMAudio("./Vine-boom-sound-effect.mp3")
                while ctx.voice_client.is_playing():
                    pass
                try:
                    ctx.voice_client.play(source)
                except Exception as e:
                    print(e)
                await ctx.send(
                    f"Hey <@{user}>, please don't swear! => `{result['text']}`"
                )


@bot.slash_command(name="stop", description="Stop recording")
async def stop(ctx: discord.ApplicationContext):
    if ctx.guild.id in connections:
        vc = connections[ctx.guild.id]
        vc.stop_recording()
        await ctx.respond("The recording has stopped!")
        del connections[ctx.guild.id]
    else:
        await ctx.send("Not recording in this guild.")


# Run the bot
bot.run(os.getenv("DISCORD_BOT_TOKEN"))
