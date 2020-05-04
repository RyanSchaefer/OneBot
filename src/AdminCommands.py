from typing import List, Dict

import discord
from discord.ext import commands

from NoConflictCog import NoConflictCog


class AdminCommands(NoConflictCog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.__sudoers: List[discord.User] = []

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.message.author) or ctx.message.author in self.__sudoers

    @commands.command()
    async def testing_mode(self, ctx: commands.Context, enable_p: bool):
        """
        Enable testing mode for the bot, will allow the bot to reply to other bots
        :param enable_p: should testing mode be enabled?
        """
        if ctx.bot:
            bot: commands.Bot = ctx.bot
            if enable_p:
                bot.unload_extension("SafetyChecks")
                await ctx.send("Testing mode enabled! Safety Checks removed.")
            else:
                bot.load_extension("SafetyChecks")
                await ctx.send("Testing mode disabled. Safety Checks reinstated.")
        else:
            await ctx.send("Something went wrong")

    @commands.command()
    async def kill(self, ctx: commands.Context):
        """
        Kill the bot
        """
        await ctx.bot.close()

    @commands.command()
    async def purge(self, ctx: commands.Context):
        """
        Purge all messages from the channel
        """
        await ctx.channel.purge()

    @commands.command()
    async def loaded_extensions(self, ctx: commands.Context):
        """
        Get a list of all of the extensions loaded
        """
        await ctx.send(f"{', '.join(self.bot.extensions)}")

    @commands.command()
    async def reload_extension(self, ctx: commands.Context, extension: str):
        """
        Reload the given extension
        :param extension: the extension to reload (can be gotten from loaded_extensions)
        """
        try:
            self.bot.reload_extension(extension)
            await ctx.send(f"{extension} reloaded.")
        except Exception as e:
            await ctx.send("Extension could not be reloaded.")
            raise e

    @commands.command()
    async def add_sudoer(self, ctx: commands.Context, user: discord.User):
        """
        Add a sudoer to the bot
        :param user: the user to add (can be mentioned, by username with discriminator, or by id)
        """
        if user not in self.__sudoers:
            self.__sudoers.append(user)
            await ctx.send(f"User {user} was added to the sudoers.")

    @commands.command()
    async def remove_sudoer(self, ctx: commands.Context, user: discord.User):
        """
        Remove a sudoer from the bot
        :param user: the user to remove (can be mentioned, by username with discriminator, or by id)
        """
        if user in self.__sudoers:
            self.__sudoers.remove(user)
            await ctx.send(f"User {user} was removed from sudoers.$")
        else:
            await ctx.send(f"User {user} is not a sudoer")

    @commands.command()
    async def status(self, ctx: commands.Context):
        await ctx.send(f"Sudoers: {', '.join([str(x) for x in self.__sudoers])}")

    @commands.command()
    async def load_extension(self, ctx: commands.Context, extension):
        """
        Loads an extension to the bot
        :param extension: the extension to load
        """
        try:
            self.bot.load_extension(extension)
            await ctx.send(f"{extension} successfully loaded")
        except Exception as e:
            await ctx.send(f"Could not load {extension}")
            raise e

    @commands.command()
    async def available_commands(self, ctx: commands.Context):
        cogs: Dict[str, commands.Cog] = self.bot.cogs
        print(cogs)
        ret: str = ""
        key: str
        cog: commands.Cog
        for key, cog in cogs.items():
            ret += f"{cog.qualified_name}\r"
            command: commands.Command
            for command in cog.get_commands():
                ret += f"\t{command.qualified_name}\r"
        await ctx.send(ret)


def setup(bot: commands.Bot):
    bot.add_cog(AdminCommands(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("AdminCommands")
