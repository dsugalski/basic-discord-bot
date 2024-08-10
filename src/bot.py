import discord
import os
import psutil

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from src.database.database import Database
from src.logging import logger
from src.utils.config import Config
from src.utils.stats import StatsTracker

intents = discord.Intents.all()
if hasattr(intents, "message_content"):
    intents.message_content = True

def mem_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss

class MyBot(commands.Bot):
    def __init__(self, command_prefix="$", description="simple discord bot",
                 app_id=-1):
        super(MyBot, self).__init__(command_prefix=command_prefix,
                                    help_command=None,
                                    case_insensitive=True,
                                    description=description,
                                    intents=intents,
                                    application_id=app_id)

        self.token = os.getenv("DISCORD_TOKEN", "<no token>")

        self.database = Database()
        self.database.safe_start()
        self.engine = self.database.engine # A handy little shortcut

        self.sched = AsyncIOScheduler(timezone='utc')

        self.config = Config(self)
        self.stats = StatsTracker(self)

    async def on_ready(self):

        # Bot is ready. Load in all the cogs.
        cogs = [name for name in os.listdir("./src/cogs")
                if name.endswith(".py")
                and not name.startswith("_")
                and not name.startswith("#")
                and not name.startswith("~")]
        cogs.sort()
        for cog in cogs:
            try:
                before = mem_usage()
                await self.load_extension(f"src.cogs.{cog[:-3]}")
                after = mem_usage()
                mem_diff = after - before
                logger.debug(f"{cog} loaded, {mem_diff:,} bytes of memory used")
            except Exception as e:
                logger.warning("{}: {}".format(type(e).__name__, e), exc_info=True)

        # Now that the cogs are ready we can start up the
        # scheduler. We wait until after cog load in case cogs have
        # installed timer things -- we don't want timers firing while
        # we're still initializing.
        self.sched.start()

        logger.info("Bot ready")

    def run(self):
        super().run(self.token, reconnect=True)        
