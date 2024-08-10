import discord
import logging
import os
import traceback

from discord.ext import commands
from discord.ext.commands import errors
from dotenv import load_dotenv

from src.logging import logger
from src.bot import MyBot

load_dotenv()

prefix = os.getenv("PREFIX", "$")
if len(prefix) > 1:
    prefix = [c for c in prefix]
description = os.getenv("DESCRIPTION", "Example bot")
app_id = os.getenv("APPLICATION_ID", -1)

mybot = MyBot(command_prefix=prefix, description=description, app_id=app_id)

@mybot.event
async def on_command_error(ctx: commands.Context, exception:errors.CommandError) -> None:
    """
       Handler for errors caught when parsing or executing a command.

       This handler overrides the default handler which just quietly emits
       a message to the log.
    """
    logger.exception(exception, exc_info=True)
    if isinstance(exception, errors.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
        return
    elif isinstance(exception, errors.CommandNotFound):
        await ctx.send("Unknown command")
        return
    
    await ctx.send(f"Error handling that command: {exception}")

@mybot.command(name="sync")
@commands.has_permissions(manage_guild=True)
async def sync_slash(ctx: commands.Context):
    synced = await mybot.tree.sync()
    await ctx.send(f"Sync status: {len(synced)} slash commands sync'd")

if __name__ == '__main__':
    mybot.run()
