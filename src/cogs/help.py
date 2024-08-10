import discord

from discord.ext import commands
from typing import Optional

class Help(commands.Cog):
    """
        Help command group.

        This group holds the help command. For more help on help, try `help help`.
    """

    def __init__(self, bot):
        self.bot = bot
        self.hidden = False

    @commands.command(name="help")
    async def help(self, ctx: commands.Context, *, commandlist: Optional[str]):
        """
           Displays help for commands.

           Help with no parameters will show the summary for all user-visible
           command groups. Help with a parameter list will show the help
           for that command or command set.

           **Usage:** `help [command]`

           **Example:** `help timer`
        """
        # Is this a summary invocation?
        if commandlist is None or len(commandlist) == 0:
            embeds = []
            embed = discord.Embed(title="Help for command groups")
            fields = 0
            curlen = 0
            coglist = [cog for cog in self.bot.cogs]
            coglist.sort()
            for cogname in coglist:
                cog = self.bot.get_cog(cogname)
                # Is it a hidden cog? If so we skip it. This is a reasonable
                # spot to add a permissions check so folks with privs can
                # see the command.
                if cog.hidden:
                    continue

                desc = cog.description
                # We truncate descriptions to 3k characters.
                if len(desc) > 3000:
                    desc = desc[:3000]
                    
                # Will we exceed 3.5K of text with this? If so we need a new
                # embed.
                if curlen + len(desc) > 3500:
                    embeds.append(embed)
                    embed = discord.Embed()
                    fields = 0
                    curlen = 0

                embed.add_field(name=cogname, value=desc, inline=False)
                fields = fields + 1
                curlen = curlen + len(desc)

            embeds.append(embed)

            # Now that we have our embeds we send them. We send one
            # per message, so as not to blow discord's max-JSON-len
            # checks.
            for e in embeds:
                await ctx.send(embed=e)

            return

        # Not a summary invocation, so presumably they gave us a
        # command to look for.
        command = self.bot.get_command(commandlist)
        if command is None or command.hidden:
            await ctx.send(f"I have no help for {commandlist}")
            return

        embed = discord.Embed(title=f"help for the `{command.qualified_name}` command")
        desc = command.help
        if len(desc) > 3000:
            desc = desc[:3000]
        embed.add_field(name=command.name, value=desc, inline=False)

        # Is this a group? Then it has children. Walk those and add
        # them to the output.
        if isinstance(command, commands.Group):
            sc = [subcommand.name for subcommand in command.walk_commands()
                  if not subcommand.hidden and subcommand.parents[0] == command]
            sc.sort()
            embed.add_field(name="Subcommands", value=", ".join([f"**{name}**" for name in sc]), inline=False)
            embed.add_field(name="More details", value=f"use `help {command.name} <subcommand>` to see more details", inline=False)
        await ctx.send(embed=embed)
            

async def setup(bot):
    await bot.add_cog(Help(bot))
    
