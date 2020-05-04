from discord.ext import commands


class SafetyChecks(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.bot.add_check(self.check_human)

    @staticmethod
    def check_human(ctx: commands.Context) -> bool:
        return not ctx.message.author.bot

    def cog_unload(self) -> None:
        self.bot.remove_check(self.check_human)



def setup(bot: commands.Bot):
    bot.add_cog(SafetyChecks(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("SafetyChecks")
