import sys

from typing import Dict

from discord.ext import commands
import discord
import typing


class MyDiscordBot(commands.Bot):
    """
    Subclass of discord bot to override the behavior which blocks responses to other bots
    """

    def __init__(self, guild, **options):
        super().__init__(**options)
        self.guild = guild
        self.key: typing.Optional[str] = None

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    @property
    def guilds(self):
        return [self.guild]

    def upgrade_to_premium(self):
        if self.key:
            pass
        raise ValueError("A key must be supplied before the bot can be upgraded to premium")


class MainBot(commands.Bot):

    def __init__(self, **options):
        super().__init__(**options)
        self.__bots: Dict[discord.Guild, MyDiscordBot] = {}

    async def process_commands(self, message):
        guild: discord.Guild = message.guild
        if guild in self.__bots:
            ctx = await self.__bots[guild].get_context(message)
            await self.__bots[guild].invoke(ctx)
        elif guild is None:
            await self.invoke(await self.get_context(message))
        else:
            bot = MyDiscordBot(message.guild, command_prefix="$")

            # we have to copy the old connection and http handler over to the new bot
            bot._connection = self._connection
            bot.http = self.http
            bot.owner_id = guild.owner_id

            bot.load_extension("AdminCommands")
            bot.load_extension("SafetyChecks")
            self.__bots[guild] = bot
            await bot.invoke(await bot.get_context(message))


client = MainBot(command_prefix="$")

client.load_extension("AdminCommands")
client.load_extension("SafetyChecks")
client.run(sys.argv[1])

