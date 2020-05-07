from typing import Set, Dict, Optional, Union

import discord
from discord.ext import commands
from types import MethodType

from discord.ext.commands import NoPrivateMessage, MissingRole

from NoConflictCog import NoConflictCog
from bot import MyDiscordBot


class AdminCommands(NoConflictCog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.__protections: Dict[str, Set[Union[discord.Role, discord.User]]] = {
            self.qualified_name: set()
        }
        self.__roles: Dict[str, discord.role] = {}
        self.__SUPER_USER_ROLE_NAME = "SuperUser"

    async def cog_before_invoke(self, ctx):
        if self.__roles == {}:
            role: discord.Role
            for role in ctx.guild.roles:
                self.__roles[role.name] = role
        server: discord.Guild = ctx.guild
        if self.__SUPER_USER_ROLE_NAME not in self.__roles:
            role: discord.Role = await server.create_role(
                name=self.__SUPER_USER_ROLE_NAME,
                reason="Super User Group was created from the super user command",
                permissions=discord.Permissions.general()
            )
            self.__roles[role.name] = role
        if await self.bot.fetch_user(self.bot.owner_id) not in self.__protections[self.qualified_name]:
            self.__protections[self.qualified_name].add(await self.bot.fetch_user(self.bot.owner_id))
        if self.__SUPER_USER_ROLE_NAME not in self.__protections[self.qualified_name]:
            self.__protections[self.qualified_name].add(self.__roles[self.__SUPER_USER_ROLE_NAME])

    async def bot_check(self, ctx: commands.Context) -> bool:
        cog: commands.Cog = ctx.cog
        if cog.qualified_name in self.__protections:
            return ctx.author in self.__protections[cog.qualified_name] or self.__protections[cog.qualified_name]\
                .difference(set(ctx.author.roles)) is not None or await self.bot.is_owner(ctx.author)
        else:
            return await self.bot.is_owner(ctx.author)

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
        await ctx.send(f"{', '.join(ctx.bot.extensions)}")

    @commands.command()
    async def reload_extension(self, ctx: commands.Context, extension: str):
        """
        Reload the given extension
        :param extension: the extension to reload (can be gotten from loaded_extensions)
        """
        try:
            ctx.bot.reload_extension(extension)
            await ctx.send(f"{extension} reloaded.")
        except Exception as e:
            await ctx.send("Extension could not be reloaded.")
            raise e

    @commands.guild_only()
    @commands.command()
    async def add_su(self, ctx: commands.Context, user: discord.Member):
        """
        Add a sudoer to the bot
        :param user: the user to add (can be mentioned, by username with discriminator, or by id)
        """
        if self.__roles[self.__SUPER_USER_ROLE_NAME] not in ctx.author.roles:
            await user.add_roles(self.__roles[self.__SUPER_USER_ROLE_NAME])
            await ctx.send(f"User {user} was added to the sudoers.")
        if self.__roles[self.__SUPER_USER_ROLE_NAME] not in self.__protections[self.qualified_name]:
            self.__protections[self.qualified_name].add(self.__roles[self.__SUPER_USER_ROLE_NAME])

    @commands.guild_only()
    @commands.command()
    async def remove_su(self, ctx: commands.Context, user: discord.Member):
        """
        Remove a sudoer from the bot
        :param user: the user to remove (can be mentioned, by username with discriminator, or by id)
        """
        server: discord.Guild = ctx.guild
        if self.__SUPER_USER_ROLE_NAME not in self.__roles:
            await ctx.send("There are no suers yet.")
        if self.__roles[self.__SUPER_USER_ROLE_NAME] in ctx.author.roles:
            await ctx.author.remove_roles(self.__roles[self.__SUPER_USER_ROLE_NAME])
            await ctx.send(f"User {user} was removed from sudoers.")
        else:
            await ctx.send(f"User {user} is not a sudoer")

    @commands.command()
    async def status(self, ctx: commands.Context):
        ret = "Current protections:\r"
        for protection in self.__protections:
            ret += f"{protection}\r"
            for accessor in self.__protections[protection]:
                ret += f"\t{accessor}\r"
        await ctx.send(ret)

    @commands.command()
    async def load_extension(self, ctx: commands.Context, extension):
        """
        Loads an extension to the bot
        :param extension: the extension to load
        """
        try:
            ctx.bot.load_extension(extension)
            await ctx.send(f"{extension} successfully loaded")
        except Exception as e:
            await ctx.send(f"Could not load {extension}")
            raise e

    @commands.command()
    async def available_commands(self, ctx: commands.Context):
        cogs: Dict[str, commands.Cog] = ctx.bot.cogs
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

    @commands.command()
    async def protect_cog(self, ctx: commands.Context, cog_name: str, role: Optional[Union[int, str]]):
        # check that the cog name exists
        if cog_name in ctx.bot.cogs:
            cog: commands.Cog = ctx.bot.get_cog(cog_name)
            old_check = cog.cog_check.__func__
            if not role:
                # if a role was not supplied assume that the user wants to restrict usage of the cog to only sudoers
                @commands.cog._cog_special_method
                # this is required to be called because overridden cog methods have a special private attribute added to
                # them
                def __check(func, cog_self: commands.Cog, ctx: commands.Context) -> bool:
                    """
                    This function wraps an existing cog check with a new one
                    :param func: the old cog check to wrap
                    :param cog_self: the cog the check came from
                    :param ctx: the context we are supplying to the check
                    """
                    bot: commands.Bot = ctx.bot
                    admin: 'AdminCommands' = bot.get_cog("AdminCommands")
                    if admin:
                        # if we have loaded the command we can check that the author is in the sudoers
                        # AND that they passed the original check
                        return ctx.author in admin.sudoers and func(cog_self, ctx)
                    # we cannot do anything if AdminCommands is not loaded
                    return func(cog_self, ctx)

                # This nasty little piece of work is required to dynamically change the method to our new method we
                # specified
                cog.cog_check = MethodType(
                    lambda cog_self, context: __check(old_check, cog_self, context),
                    cog)

                await ctx.send(f"{cog_name} protected")
            if role:
                @commands.cog._cog_special_method
                def __role_check(func, cog_self: commands.Cog, ctx: commands.Context, role) -> bool:
                    if not isinstance(ctx.channel, discord.abc.GuildChannel):
                        raise NoPrivateMessage()
                    if isinstance(role, int):
                        r = discord.utils.get(ctx.author.__roles, id=role)
                    else:
                        r = discord.utils.get(ctx.author.__roles, name=role)
                    if r is None:
                        raise MissingRole(role)
                    return func(cog_self, ctx)

                cog.cog_check = cog.cog_check = MethodType(
                    lambda cog_self, context: __role_check(old_check, cog_self, context, role),
                    cog)
                await ctx.send(f"{cog_name} protected")
        else:
            await ctx.send("That cog does not exist or is not loaded")

    @commands.is_owner()
    @commands.command()
    async def print(self, ctx: commands.Context):
        print(await self.bot.fetch_user(self.bot.owner_id))


def setup(bot: commands.Bot):
    bot.add_cog(AdminCommands(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("AdminCommands")
