import sys
from enum import Enum, auto

from discord.ext import commands


class Settings(Enum):
    testing_enabled = auto()


class MyDiscordBot(commands.Bot):
    """
    Subclass of discord bot to override the behavior which blocks responses to other bots
    """

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)


client = MyDiscordBot(command_prefix="$")

client.load_extension("AdminCommands")
client.load_extension("SafetyChecks")
client.run(sys.argv[1])

