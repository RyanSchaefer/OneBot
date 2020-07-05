from typing import Set, Dict, Optional, Union

import discord
from discord.ext import commands
import pickle
from types import MethodType

from discord.ext.commands import NoPrivateMessage, MissingRole

from NoConflictCog import NoConflictCog
from bot import MyDiscordBot
from os import path, makedirs


# TODO: Add protections for single command
#   This will most likely be implemented in the same protections namespace but with a prefix for the cog
# TODO: Add protection of command to channel
#   Should just be an expansion of the Union for the mapping of __protections
# TODO: add "installation" for packaged Extensions that have been vetted
#   This will require some vetting process and repository for storing them
#   Look into how to have such a repository, services or open source
# TODO: (Not priority) Add ability to separate bot into space that can add non-vetted extensions
#   User would need a subscription to cover the server costs or some other way to monetize (patreon?)
#   Most likely another subclass in main.bot
#   Look at stripe for payment processing


class AdminCommands(NoConflictCog):

    def __init__(self, bot):
        self.bot: MyDiscordBot = bot
        self.__roles: Dict[str, discord.role] = {}
        self.__SUPER_USER_ROLE_NAME = "SuperUser"
        self.__protections: Dict[str, Set[Union[discord.Role, discord.User]]] = {
            self.qualified_name: set()
        }
        self.__protections_checked = False

    async def __load_protections(self):
        """
        If existing protections exist in the folder add them to be able to protect the cogs on the bot
        """
        try:
            try:
                config: Dict[str, Set[int]] = pickle.load(
                    open(path.join("..", str(self.bot.guilds[0].id), self.qualified_name), 'rb'))
                for protection in config:
                    for snowflake in config[protection]:
                        try:
                            self.__protections.setdefault(protection, set()).add(await self.bot.fetch_user(snowflake))
                        except discord.NotFound:
                            self.__protections[protection].add(self.bot.guilds[0].get_role(snowflake))
            except FileNotFoundError:
                self.__protections: Dict[str, Set[Union[discord.Role, discord.User]]] = {
                    self.qualified_name: set()
                }
        except IndexError:
            print("index error")

    def __save_protections(self):
        """
        Save existing protections to disk
        """
        filename = path.join("..", str(self.bot.guilds[0].id), self.qualified_name)
        makedirs(path.dirname(filename), exist_ok=True)
        config: Dict[str, Set[int]] = {}
        protection: str
        for protection in self.__protections:
            config[protection] = set(map(lambda x: x.id, self.__protections[protection]))
        pickle.dump(config, open(filename, 'wb'))

    async def cog_before_invoke(self, ctx):
        """
        Before a command within this cog is invoked check if protections have been loaded and if they have not been
        load them
        TODO: Might have to move the loading to before any command within the given bot is loaded
        :param ctx:
        """
        if not self.__protections_checked:
            self.__protections_checked = True
            await self.__load_protections()
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
        """
        Handles the checking of protections on commands and cogs
        :return:
        """
        cog: commands.Cog = ctx.cog
        command: commands.Command = ctx.command

        if ctx.channel is not None and cog is not None:
            if cog.qualified_name in self.__protections:
                return ctx.author in self.__protections[cog.qualified_name] or self.__protections[cog.qualified_name] \
                    .difference(set(ctx.author.roles)) is not None or await self.bot.is_owner(ctx.author)
        else:
            return await self.bot.is_owner(ctx.author)

    async def cog_check(self, ctx):
        return ctx.guild is not None

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
        """
        What are the protections loaded onto the bot?
        :param ctx:
        :return:
        """
        ret = "Current protections:\r"
        end = "Unprotected cogs:\r"
        for cog in self.bot.cogs:
            if cog in self.__protections:
                ret += f"{cog}\r"
                for accessor in self.__protections[cog]:
                    ret += f"\t{accessor}\r"
            else:
                end += f"{cog}\r"
        await ctx.send(ret + end)

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
        """
        What commands are available for the user to use?
        :param ctx:
        :return:
        """
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

    @commands.guild_only()
    @commands.command()
    async def protect_cog(self, ctx: commands.Context, cog_name: str,
                          role: Optional[Union[discord.Role, discord.User]]):
        """
        Protect a cog to a given role
        :param ctx:
        :param cog_name:
        :param role: if None, protect the role to the super user group, else protect to the role or user given
        :return:
        """
        if self.bot.get_cog(cog_name) is not None:
            protections = self.__protections.setdefault(cog_name, set())
            super_user_role = self.__roles[self.__SUPER_USER_ROLE_NAME]
            if role is None and super_user_role not in protections:
                protections.add(super_user_role)
                await ctx.send(f"{cog_name} is protected to group {self.__SUPER_USER_ROLE_NAME}")
            elif role is None and super_user_role in protections:
                await ctx.send(f"{cog_name} is protected to group {self.__SUPER_USER_ROLE_NAME}")
            elif role is not None and role not in protections:
                protections.add(role)
                await ctx.send(f"{cog_name} is protected to {role.name}")
        else:
            await ctx.send(f"{cog_name} does not exist")
        self.__save_protections()

    @protect_cog.error
    async def protect_cog_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find user or role")

    @commands.command()
    async def remove_cog_protection(self, ctx: commands.Context, cog_name: str,
                                    role: Optional[Union[discord.Role, discord.User]]):
        """
        Remove an existing protection from the bot
        :param ctx:
        :param cog_name: the cog to "unprotect"
        :param role: if None, remove all protections from the given cog, else attempt to remove the given role
        :return:
        """
        if cog_name in self.__protections:
            super_user_role = self.__roles[self.__SUPER_USER_ROLE_NAME]
            protections = self.__protections[cog_name]
            if role is None and super_user_role in protections:
                protections.remove(super_user_role)
                await ctx.send(f"{cog_name} unprotected from {self.__SUPER_USER_ROLE_NAME}")
            elif role is None and super_user_role not in protections:
                await ctx.send(f"Please specify a group to protect {cog_name} to")
            elif role is not None and role in protections:
                protections.add(role)
                await ctx.send(f"{cog_name} protected to {role}")
        else:
            if cog_name not in self.bot.cogs:
                await ctx.send(f"{cog_name} does not exist")
            else:
                await ctx.send(f"{cog_name} has no protections")
        self.__save_protections()

    @commands.is_owner()
    @commands.command()
    async def print(self, ctx: commands.Context):
        """
        Used only for debugging purposes
        :return:
        """
        print(ctx.command)

    @commands.command()
    async def save_config(self, ctx: commands.Context):
        """
        Since the bot cannot be reliably killed if it is in the communal bot space, we must allow the user to save
        protections at a given point in case the bot were to go down
        TODO: Possibly make this automatically called at a given interval
        TODO: Possibly support rolling back changes made within the given interval
        TODO: Maybe allow premium users to have more extensive history of saves
        :param ctx:
        :return:
        """
        self.__save_protections()

    @commands.command()
    async def protect_command(self, ctx: commands.Context):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(AdminCommands(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("AdminCommands")
