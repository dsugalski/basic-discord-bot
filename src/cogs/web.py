import asyncio
import discord
import os

from discord import Guild, Member, User
from discord.ext import commands
from hypercorn.asyncio import serve
from hypercorn.config import Config as HyperConfig
from quart import Quart, redirect, url_for, render_template, request, session, abort, send_file, send_from_directory
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from typing import Any

from src.logging import logger

WEB_SERVER_STATUS = "web:should_run"
WEB_SERVER_DEFAULT = "False"

class Web(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webserver_running = False
        self.hidden = True
        self.shutdown_event = asyncio.Event()
        self.files_served = {} # Files we'll serve from the default
                               # handler but don't want to bother
                               # installing in /static or having
                               # explicit handlers for.

        app = Quart(__name__,
                    template_folder="../web/templates",
                    static_folder="../web/static")

        app.secret_key = b"random bytes representing quart secret key"
        
        app.config["DISCORD_CLIENT_ID"] = os.getenv("APPLICATION_ID")   # Discord client ID.
        app.config["DISCORD_CLIENT_SECRET"] = os.getenv("CLIENT_SECRET")

        # URL to your callback endpoint. The default is just localhost
        # which won't work for anyone but you developing locally.
        redirect_url = os.getenv("DISCORD_REDIRECT_URL",
                                 "http://localhost:8080/callback/")
        app.config["DISCORD_REDIRECT_URI"] = redirect_url
        
        app.config["DISCORD_BOT_TOKEN"] = os.getenv("DISCORD_TOKEN")   # Required to access bot resources.

        # Uncomment to see what's going on with template loading.
        # app.config["EXPLAIN_TEMPLATE_LOADING"] = True

        app.config["TEMPLATES_AUTO_RELOAD"] = True

        discordd = DiscordOAuth2Session(app)

        self.app = app
        self.discordd = discordd
        
        # The host the bot listens on, or if not set we listen on everything.
        self.host = os.getenv("DISCORD_WEBSERVER_HOST", "0.0.0.0")
        # The host port the bot listens on, or if not set we listen on 8080
        self.port = os.getenv("DISCORD_WEBSERVER_PORT", "8080")
        # The external URL
        external_url = redirect_url.replace("/callback/",
                                            "").replace("/callback", "")
        self.access_url = os.getenv("DISCORD_WEBSERVER_URL", external_url)
        
        should_start = self.bot.config.get(-1, WEB_SERVER_STATUS,
                                           WEB_SERVER_DEFAULT)
        logger.debug(f"Web should start is {should_start}")
        if should_start == "True":
            self.start_webserver()

        # Defined inside init because we need self. This is sad and there's
        # probably a better way but it'll do for now.
        @app.route("/")
        @app.route("/index.html")
        @requires_authorization
        async def home():
            logged = ""
            if await discordd.authorized:
                logged = True
            member = None
            guild = await self.get_guild()
            cog_data = {}

            if guild is not None:
                cog_data['guild'] = guild
                member = await self.get_member(guild)
            
            return await render_template("index.html",**cog_data)
        
        @app.route("/login/")
        async def login():
            return await discordd.create_session(scope=["identify", "guilds"])

        @app.route("/logout/")
        async def logout():
            discordd.revoke()
            return redirect(url_for(".home"))
        
        @app.route("/callback/")
        async def callback():
            await discordd.callback()
            try:
                redir = session['redirect']
                del session['redirect']
                return redirect(redir)
            except:            
                return redirect("/")

        @app.errorhandler(Unauthorized)
        async def redirect_unauthorized(e):
            session['redirect'] = request.url
            return redirect(url_for("login"))

        # Yes, this duplicates the default, but without this in as an
        # explicit path handler, the catchall rule *with* the required
        # authorization does weird things when you try and log in.
        @app.route("/static/<path:path>")
        async def serve_files(path):
            return await send_from_directory("static", path)

    async def get_user(self) -> User:
        """
           Return a discord User object for the current user.
        """
        user = await self.discordd.fetch_user()
        if user is None:
            return None
        return self.bot.get_user(user.id)
            
    async def get_member(self, guild: Guild) -> Member:
        """
           return the member object for the current user in the passed
           in guild.
        """
        user = await self.discordd.fetch_user()
        if user is None:
            return None
        member = guild.get_member(user.id)
        return member

    async def get_guild(self) -> Guild:
        """
           Return a guild object for the currently selected guild
        """
        guild_id = session.get('guild_id')
        if guild_id is None:
            return None
        guild_id = int(guild_id)
        for guild in self.bot.guilds:
            if guild.id == guild_id:
                # Found the guild. is the current user a member?
                if await self.get_member(guild) is not None:
                    return guild
                else:
                    return None
        return None        

    async def get_guilds(self, user):
        """
            Return guild objects for all guilds the user is in.
        """
        guilds = []
        for guild in self.bot.guilds:
            try:
                m =  guild.get_member(user.id)
                if m is None:
                    m = await guild.fetch_member(user.id)
                if m is not None:
                    guilds.append(guild)
            except Exception as e:
                pass
        return guilds
        

    @commands.group(name="web", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def web_command(self, ctx: commands.Context):
        """
           Access the web interface.
        """
        if self.webserver_running:
            await ctx.send(f"I am listening on {self.access_url}")
        else:
            await ctx.send("My webserver isn't currently running")
            return

    @web_command.command(name="on")
    @commands.has_permissions(manage_guild=True)
    async def web_on(self, ctx: commands.Context):
        """
           Turn the web interface on
        """
        if self.webserver_running:
            await ctx.send("The webserver is already running")
            return
        self.start_webserver()
        await ctx.send("The webserver is started")
        return
        
    @web_command.command(name="off")
    @commands.has_permissions(manage_guild=True)
    async def web_off(self, ctx: commands.Context):
        """
           Turn the web interface off
        """
        if not self.webserver_running:
            await ctx.send("The webserver isn't running")
            return
        self.stop_webserver(manual_shutdown=True)
        await ctx.send("The webserver is stopped")
        return

        
    # The cog_unload is called whenever a cog is unloaded. This
    # happens when a cog is explicitly unloaded, reloaded (which is
    # just unload/load), or the server shuts down cleanly.
    def cog_unload(self):
        self.stop_webserver()

    def start_webserver(self):
        self.bot.loop.create_task(self.app.run_task(self.host, self.port,
                                                    shutdown_trigger=self.shutdown_event.wait))
        self.webserver_running = True
        self.bot.config.set(-1, WEB_SERVER_STATUS, "True")

    def stop_webserver(self, manual_shutdown=False):
        # trigger the shutdown event so the webserver, which is listening
        # on it, can cleanly shut down.
        self.shutdown_event.set()
        self.webserver_running = False
        if manual_shutdown:
            self.bot.config.set(-1, WEB_SERVER_STATUS, "False")
        
async def setup(bot):
    await bot.add_cog(Web(bot))
    

