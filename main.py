import os
import threading
import discord
from discord.ext import commands
from flask import Flask
from dotenv import load_dotenv

# Ladataan ympäristömuuttujat (.env paikallisesti tai Renderin asetuksista)
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

MEMORY_CHANNEL_NAME = "jarvis-memory"

# Discord-botin asetukset: käytetään j.-prefixiä vanhoille komennoille ja poistetaan oletus-help
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="j.", intents=intents, help_command=None)


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

# Liitetään vault-funktiot suoraan bottiin, jotta cogit pääsevät niihin käsiksi (self.bot.load_vault)
bot.load_vault = load_vault
bot.save_vault = save_vault


# --- TAPAHTUMAT JA COGIEN LATAUS ---
@bot.event
async def on_ready():
    # Ladataan automaattisesti kaikki cog-tiedostot cogs/-kansioista
    if os.path.exists("./cogs"):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                cog_name = f"cogs.{filename[:-3]}"
                if cog_name not in bot.extensions:
                    await bot.load_extension(cog_name)
                    print(f"Loaded cog: {cog_name}")

    # Synkronoidaan Slash-komennot (esim. /help) Discordiin
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    print(f"Jarvis is online as {bot.user} (Engine clean)")


# --- FLASK KEEP-ALIVE -PALVELIN (Renderiä varten) ---
app = Flask(__name__)

@app.route("/")
def home():
    return "Jarvis is awake!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN is missing from environment variables!")

    # Käynnistetään Flask taustasäikeessä, jotta botti ei sammu Renderissä
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Käynnistetään Discord-botti
    bot.run(DISCORD_TOKEN)
