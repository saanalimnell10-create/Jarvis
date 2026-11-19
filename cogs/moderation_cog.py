import discord
from discord.ext import commands

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- PING / STATUS ---
    @commands.command(name="ping")
    async def prefix_ping(self, ctx: commands.Context):
        await ctx.send("Jarvis moderation engine: Online.")

    # --- PURGE ---
    @commands.command(name="purge", aliases=["clear"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, limit: int = 10):
        await ctx.message.delete()
        deleted = await ctx.channel.purge(limit=limit)
        msg = await ctx.send(f"🧹 Poistettu {len(deleted)} viestiä.")
        await msg.delete(delay=3)

    # --- KICK ---
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Ei syytä annettu"):
        await member.kick(reason=reason)
        await ctx.send(f"🔨 Potkittu ulos: {member.mention}. Syy: {reason}")

    # --- BAN ---
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Ei syytä annettu"):
        await member.ban(reason=reason)
        await ctx.send(f"⛔ Porttikiellon saanut: {member.mention}. Syy: {reason}")

    # --- TIMEOUT / MUTE ---
    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, minutes: int, *, reason: str = "Ei syytä annettu"):
        duration = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 Hiljennetty: {member.mention} ajaksi {minutes} min. Syy: {reason}")

    # --- UNMUTE ---
    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f"🔊 Poistettu mykistys: {member.mention}")

    # --- WARN ---
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str):
        try:
            await member.send(f"⚠️ Olet saanut varoituksen palvelimella **{ctx.guild.name}**.\nSyy: {reason}")
            await ctx.send(f"⚠️ Varoitus lähetetty käyttäjälle {member.mention}. Syy: {reason}")
        except discord.Forbidden:
            await ctx.send(f"⚠️ Varoitus annettu käyttäjälle {member.mention} (Ei voitu lähettää yksityisviestiä). Syy: {reason}")

    # --- LOCKDOWN ---
    @commands.command(name="lockdown")
    @commands.has_permissions(manage_channels=True)
    async def lockdown(self, ctx: commands.Context):
        channel = ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        # If send_messages is True or None, lock it down. Otherwise, unlock it.
        if overwrite.send_messages is False:
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send(f"🔓 Kanava **{channel.name}** on avattu uudelleen.")
        else:
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
            await ctx.send(f"🔒 Kanava **{channel.name}** on lukittu.")

    @lockdown.error
    async def lockdown_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Sinulla ei ole oikeuksia hallita kanavia.")


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
