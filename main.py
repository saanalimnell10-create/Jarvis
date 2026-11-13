import os
import json
import threading
import discord
from discord.ext import commands
from flask import Flask
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Ladataan ympäristömuuttujat (.env paikallisesti tai Renderin asetuksista)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MEMORY_CHANNEL_NAME = "jarvis-memory"

# Alustetaan Gemini AI (jos API-avain on asetettu)
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

JARVIS_SYSTEM_PROMPT = (
    "You are Jarvis, a personal AI assistant. Use a calm, literal, direct, and "
    "zero-guilt tone. Never judge, lecture, or use harsh language. Keep explanations "
    "clear and structured, and break overwhelming tasks into tiny, low-pressure 2-minute steps."
)

# Discord-botin asetukset
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# --- TIETOKANTA DISCORDIN KANAVALLA (#jarvis-memory) ---
async def load_vault(guild: discord.Guild, vault_name: str, default_data: dict) -> dict:
    channel = discord.utils.get(guild.text_channels, name=MEMORY_CHANNEL_NAME)
    if not channel:
        return default_data

    pins = await channel.pins()
    for msg in pins:
        if msg.content.startswith(f"VAULT:{vault_name}\n"):
            raw_json = msg.content.split("\n", 1)[1].strip("`json\n ")
            try:
                return json.loads(raw_json)
            except json.JSONDecodeError:
                return default_data

    # Luodaan ja kiinnitetään viesti, jos sitä ei vielä ole
    formatted = f"VAULT:{vault_name}\n```json\n{json.dumps(default_data, indent=2)}\n```"
    new_msg = await channel.send(formatted)
    await new_msg.pin()
    return default_data


async def save_vault(guild: discord.Guild, vault_name: str, data: dict) -> None:
    channel = discord.utils.get(guild.text_channels, name=MEMORY_CHANNEL_NAME)
    if not channel:
        return

    formatted = f"VAULT:{vault_name}\n```json\n{json.dumps(data, indent=2)}\n```"
    pins = await channel.pins()
    for msg in pins:
        if msg.content.startswith(f"VAULT:{vault_name}\n"):
            await msg.edit(content=formatted)
            return


# --- TAPAHTUMAT JA NORMAALI JUTTELU ---
@bot.event
async def on_ready():
    print(f"Jarvis on linjoilla nimellä {bot.user}")


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.content.startswith("!"):
        await bot.process_commands(message)
        return

    # Kanavat, joilla voi jutella normaalisti ilman !-komentoja
    chat_channels = {"general", "vent-buffer", "food-and-tasks"}
    if message.channel.name in chat_channels:
        if not ai_client:
            await message.channel.send(
                "Gemini API -avain puuttuu vielä — lisää `GEMINI_API_KEY`, niin normaali juttelu toimii!"
            )
            return

        async with message.channel.typing():
            try:
                response = await ai_client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=message.content,
                    config=types.GenerateContentConfig(
                        system_instruction=JARVIS_SYSTEM_PROMPT,
                    ),
                )
                reply_text = response.text or "En saanut tuosta kiinni — kokeiletko uudestaan?"
                for i in range(0, len(reply_text), 1900):
                    await message.channel.send(reply_text[i : i + 1900])
            except Exception as e:
                await message.channel.send(f"Virhe Gemini-yhteydessä: `{e}`")


# --- PERUSKOMENNOT ---
@bot.command()
async def ping(ctx: commands.Context):
    await ctx.send("Online and ready.")


@bot.command()
async def cuddle(ctx: commands.Context):
    data = await load_vault(ctx.guild, "affection_jar", {"cuddles": 0, "kisses": 0})
    data["cuddles"] += 1
    await save_vault(ctx.guild, "affection_jar", data)
    await ctx.send(
        f"Banked a cuddle. (Total in jar: **{data['cuddles']}** cuddles, **{data['kisses']}** kisses)"
    )


@bot.command()
async def kiss(ctx: commands.Context):
    data = await load_vault(ctx.guild, "affection_jar", {"cuddles": 0, "kisses": 0})
    data["kisses"] += 1
    await save_vault(ctx.guild, "affection_jar", data)
    await ctx.send(
        f"Banked a kiss. (Total in jar: **{data['cuddles']}** cuddles, **{data['kisses']}** kisses)"
    )


@bot.command()
async def bundle(ctx: commands.Context):
    data = await load_vault(ctx.guild, "affection_jar", {"cuddles": 0, "kisses": 0})
    if data["cuddles"] == 0 and data["kisses"] == 0:
        await ctx.send("Your affection jar is empty right now.")
        return

    msg = f"Sending you a bundle of {data['cuddles']} cuddles and {data['kisses']} kisses I saved up for you! ❤️"
    await ctx.send(f"Copy and send this when she's free:\n> {msg}")

    await save_vault(ctx.guild, "affection_jar", {"cuddles": 0, "kisses": 0})


# --- FLASK KEEP-ALIVE -PALVELIN ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Jarvis is awake!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN puuttuu ympäristömuuttujista!")

    # Käynnistetään Flask taustasäikeessä
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Käynnistetään Discord-botti
    bot.run(DISCORD_TOKEN)
