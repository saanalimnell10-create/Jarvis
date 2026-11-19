import discord
from discord import app_commands
from discord.ext import commands

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.current_page = "home"

    async def show_page(self, interaction: discord.Interaction, page: str):
        self.current_page = page
        # Futuristinen sininen teemaväri tähän hätään
        embed = discord.Embed(color=discord.Color(0x00BFFF))

        if page == "home":
            embed.title = "🤖 Jarvis — Control Center"
            embed.description = (
                "Welcome to the Jarvis interactive help menu!\n\n"
                "Select a category from the dropdown menu below or use the navigation buttons."
            )
            embed.add_field(name="🧠 Persona & Memory", value="Customize how Jarvis acts and what it remembers.", inline=False)
            embed.add_field(name="⚙️ Settings & Channels", value="Manage allowed channels and check server status.", inline=False)
            embed.add_field(name="📜 All Commands", value="View a full list of available commands.", inline=False)

        elif page == "persona":
            embed.title = "🧠 Persona & Memory"
            embed.description = "Customize Jarvis's behavior specifically for this server:"
            embed.add_field(name="`/jarvis persona [description]`", value="Sets Jarvis's personality and tone.", inline=False)
            embed.add_field(name="`/jarvis remember [info]`", value="Saves a custom memory or rule for this server.", inline=False)

        elif page == "settings":
            embed.title = "⚙️ Settings & Channels"
            embed.description = "Server-specific management commands:"
            embed.add_field(name="`/jarvis settings`", value="Displays the current configuration for this server.", inline=False)
            embed.add_field(name="`/jarvis channel`", value="Toggles whether Jarvis is allowed to respond in this channel.", inline=False)

        elif page == "all":
            embed.title = "📜 All Commands"
            embed.description = "Here are all currently active commands:"
            for command in self.bot.tree.get_commands():
                if isinstance(command, app_commands.Group):
                    sub_commands = [f"`/{command.name} {sub.name}` — {sub.description}" for sub in command.commands]
                    embed.add_field(name=f"📁 /{command.name}", value="\n".join(sub_commands), inline=False)
                else:
                    embed.add_field(name=f"🔹 /{command.name}", value=command.description, inline=False)

        embed.set_footer(text=f"Page: {page.capitalize()} • Jarvis AI Bot")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.select(
        placeholder="📂 Select a category...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Home", description="Return to the main overview", emoji="🏠", value="home"),
            discord.SelectOption(label="Persona & Memory", description="Personality and server memories", emoji="🧠", value="persona"),
            discord.SelectOption(label="Settings", description="Channels and server configs", emoji="⚙️", value="settings"),
            discord.SelectOption(label="All Commands", description="List every command", emoji="📜", value="all"),
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await self.show_page(interaction, select.values[0])

    @discord.ui.button(label="Home", style=discord.ButtonStyle.secondary, emoji="🏠", row=1)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.show_page(interaction, "home")

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🗑️", row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Opens the interactive Jarvis help menu")
    @app_commands.describe(command="Search for instructions on a specific command")
    async def help_command(self, interaction: discord.Interaction, command: str = None):
        if command:
            found = None
            for cmd in self.bot.tree.get_commands():
                if cmd.name == command:
                    found = cmd
                    break
            
            if found:
                embed = discord.Embed(title=f"🔍 Command Help: /{found.name}", description=found.description, color=discord.Color(0x00BFFF))
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Command `/{command}` not found.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🤖 Jarvis — Control Center",
            description=(
                "Welcome to the Jarvis interactive help menu!\n\n"
                "Use the **dropdown menu** or **buttons** below to browse different sections."
            ),
            color=discord.Color(0x00BFFF)
        )
        embed.set_footer(text="Jarvis AI • Menu closes automatically after 2 minutes")
        view = HelpView(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
