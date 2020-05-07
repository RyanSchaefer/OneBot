import sys

from typing import Dict

from discord.ext import commands
import discord



class MyDiscordBot(commands.Bot):
    """
    Subclass of discord bot to override the behavior which blocks responses to other bots
    """

    def __init__(self, **options):
        super().__init__(**options)

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)


class MainBot(commands.Bot):

    def __init__(self, **options):
        super().__init__(**options)
        self.__bots: Dict[discord.Guild, commands.Bot] = {}

    async def process_commands(self, message):
        guild = message.guild
        if guild in self.__bots:
            ctx = await self.__bots[guild].get_context(message)
            await self.__bots[guild].invoke(ctx)
        elif guild is None:
            await self.invoke(await self.get_context(message))
        else:
            bot = MyDiscordBot(command_prefix="$")

            # we have to copy the old connection and http handler over to the new bot
            bot._connection = self._connection
            bot.http = self.http

            bot.load_extension("AdminCommands")
            bot.load_extension("SafetyChecks")
            self.__bots[guild] = bot
            await bot.invoke(await bot.get_context(message))

    async def close(self):
        await super(MainBot, self).close()


client = MainBot(command_prefix="$")

client.load_extension("AdminCommands")
client.load_extension("SafetyChecks")
client.run(sys.argv[1])

