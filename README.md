# A basic discord bot

This is the skeleton of a discord bot, suitable for tweaking,
extending, and messing around with.

Adding commands is simple (drop the code in the `src/cogs`
directory, following the templates in there) and allows dynamic
loading, unloading, reloading, and upgrading of parts of the bot
without requiring a restart.

This bot also has a very skeleton internal webserver, managed by the
web cog in `src/cogs/web.py`. There's not much to this but, since
getting properly authenticated access to discord in a webserver is a
bit of a pain and not well documented, you may find it handy if you
want to add a web interface to your bot.

## Setup

In the directory you want to put the bot framework:

```
git clone https://github.com/dsugalski/basic-discord-bot.git
cd basic-discord-bot
python3 -m pip install -r requirements.txt
```

### Creating a test discord server

You'll want to [set up a test discord
server](https://www.pythondiscord.com/pages/guides/pydis-guides/contributing/setting-test-server-and-bot-account/). These
are cheap and easy (that's cheap from a computational/resource
perspective -- they are 100% free and cost no money), and let you test
any changes locally. You only need to do this once.

### Create a test bot account

You'll need an account for the bot. There are
[instructions](https://discordpy.readthedocs.io/en/stable/discord.html)
for doing this and you'll only need to do this once. Make sure to
invite the bot to your test server.

### Configure the bot

The bot uses the [`dotenv`](https://pypi.org/project/python-dotenv/)
library to help with configuration. Normal unix practice is to put
configuration parameters as either command-line flags to a binary or
environment variables, both of which are annoying and error-prone. The
`dotenv` module lets the code use environment variables for
configuration, but you can stuff the actual settings into a file.

There is a `sample.env` file in the top level directory that has the 

`DISCORD_TOKEN`, `CLIENT_SECRET`, and `APPLICATION_ID` all are things
you'll get as you set up the bot account wiht discord, and are
required. `PREFIX` is the character that starts a command. In this
skeleton file it is the dollar sign, so you'd do things like `$help`
to invoke the help command. Change it to whatever you want, though
probably best to use something that we don't use for production.

### Develop locally

Once you have the bot configured you can start it up and do your
development. To start the bot it's:

```
python3 main.py
```

and the bot should start and then connect to your test server.

New bot cogs should go into the `src/cogs` directory. They will be
loaded at bot start, and you may reload them at any time with the `cog
load` and `cog reload` commands.

## Extra modules

The bot specifies and uses several extra modules besides discord.py to
provide a richer set of default services and capabilities. In addition
to these you may want to install the `emoji` module for Unicode emoji
handling or the `pillow` module for image manipulation.

### APScheduler

The bot uses the
[APScheduler](https://apscheduler.readthedocs.io/en/3.x/) module to
provide job scheduling services. A default scheduler is created at bot
startup time.

### SQLAlchemy

Persistent data stores are extremely useful. The bot uses the
[SQLAlchemy](https://sqlalchemy.org) ORM framework on top of a SQLite
database.

### Quart and QuartDiscord

Quart is a web framework, and QuartDiscord is an add-on to handle
discord's OAuth authentication. This is used for the bot's optional web
interface.

## References

* [Creating a bot account](https://discordpy.readthedocs.io/en/stable/discord.html)
* [Discord.py main doc page](https://discordpy.readthedocs.io/en/latest/index.html)
* [git references](https://education.github.com/git-cheat-sheet-education.pdf)
