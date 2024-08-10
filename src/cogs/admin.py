import os
import psutil

from discord.ext import commands

def mem_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss

def cleanup_name(name: str) -> str:
    """
       Cleans up the cog name. If it's missing the prefix then we give it one,
       if it's skeevy then we pitch a fit.

       This includes leading dots, double-dots, and other kinds of
       directory traversal shenanigans.
    """
    # First, just a bare name? Add the src.cogs. prefix
    if '.' not in name and '/' not in name:
        return "src.cogs."+name
    # Bad name?
    if '..' in name:
        raise NameException("Invalid cog name")
    if '//' in name:
        raise NameException("Invalid cog name")
    if name[0] == '.' or name[0] == '/':
        raise NameException("Invalid cog name")
    return name

class NameException(Exception):
    """
       Exception raised when a cog name is bad.
    """

class Admin(commands.Cog):
    """
        Administrative commands.
    """
    def __init__(self, bot):
        self.bot = bot
        self.hidden = True

    @commands.command(name="ping", description="Pings the bot")
    @commands.bot_has_permissions(send_messages=True)
    async def ping(self, ctx: commands.Context) -> None:
        """
           Pings the bot to make sure it's awake.
        """
        latency = self.bot.latency * 1000
        await ctx.send(f"{latency:.2f}ms latency")

    @commands.group(name="cog", description="Cog management commands",
                    invoke_without_command=False)
    @commands.has_permissions(manage_guild=True)
    async def admin_cog(self, ctx: commands.Context) -> None:
        """
           Cog management commands.
        """
        pass

    @admin_cog.command(name="load", description="Load a cog")
    @commands.has_permissions(manage_guild=True)
    async def admin_cog_load(self, ctx: commands.Context, cog: str) -> None:
        """
           Loads a group of commands.

           **Usage:** `cog load <cogname>`
           <cogname>: Name of the cog to load. If a bare name then the cog
                      is loaded from src.cogs.

           **Example:** `cog load help`
        """
        mem_diff = 0
        try:
            before = mem_usage()
            await self.bot.load_extension(cleanup_name(cog))
            mem_diff = mem_usage() - before
        except commands.ExtensionNotFound:
            await ctx.send(f'{cog} cannot be found.')
            return
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f'{cog} is already loaded.')
            return
        except NameException:
            await ctx.send(f'{cog} is an invalid cog name.')
            return
        await ctx.send(f'{cog} loaded, {mem_diff:,} bytes of memory used.')

    @admin_cog.command(name="reload", description="Reload a loaded cog")
    @commands.has_permissions(manage_guild=True)
    async def admin_cog_reload(self, ctx: commands.Context, cog: str) -> None:
        """
           Reoads a group of commands. If the cog was not previously loaded,
           or has been unloaded, this throws an error.

           **Usage:** `cog reload <cogname>`
           <cogname>: Name of the cog to reload. If a bare name then the cog
                      is loaded from src.cogs.

           **Example:** `cog reload help`
        """
        try:
            name = cleanup_name(cog)
        except NameException:
            await ctx.send(f'{cog} is an invalid cog name.')
            return
        
        if name not in self.bot.extensions:
            await ctx.send(f"{cog} isn't a currently loaded cog")
            return

        mem_diff = 0
        try:
            before = mem_usage()
            await self.bot.reload_extension(name)
            mem_diff = mem_usage() - before
        except commands.ExtensionNotFound:
            await ctx.send(f'{cog} cannot be found.')
            return
        except commands.ExtensionNotLoaded:
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"Unable to load cog {cog}: {e} {type(e)}")
            return

        await ctx.send(f'{cog} reloaded, {mem_diff:,} bytes of memory used')
    
    @admin_cog.command(name="unload", description="Reload a loaded cog")
    @commands.has_permissions(manage_guild=True)
    async def admin_cog_unload(self, ctx: commands.Context, cog: str) -> None:
        """
           Unload a group of commands. If the cog was not previously loaded,
           or has been unloaded, this throws an error.

           **Usage:** `cog unload <cogname>`
           <cogname>: Name of the cog to unload. If a bare name then the cog
                      is loaded from src.cogs.

           **Example:** `cog unload help`
        """
        try:
            name = cleanup_name(cog)
        except NameException:
            await ctx.send(f'{cog} is an invalid cog name.')
            return
        
        if name not in self.bot.extensions:
            await ctx.send(f"{cog} isn't a currently loaded cog")
            return

        mem_diff = 0
        try:
            await self.bot.unload_extension(name)
        except commands.ExtensionNotFound:
            await ctx.send(f'{cog} cannot be found.')
            return
        except commands.ExtensionNotLoaded:
            await self.bot.load_extension(cog)
        except Exception as e:
            await ctx.send(f"Unable to load cog {cog}: {e} {type(e)}")
            return

        await ctx.send(f'{cog} unloaded')
    

async def setup(bot):
    await bot.add_cog(Admin(bot))
