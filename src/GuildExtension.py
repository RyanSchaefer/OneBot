from datetime import datetime
from math import floor
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from NoConflictCog import NoConflictCog


class GuildExtension(NoConflictCog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.tracked_messages: \
            Dict[int, List[discord.User]] = {}
        self.watched_channels = []

    class DateTimeConverter(commands.Converter):

        async def convert(self, ctx, argument) -> datetime:
            return datetime.strptime(argument, "%m/%d")

    @commands.command()
    async def split(self,
                    ctx: commands.Context,
                    amount: int,
                    date: Optional[DateTimeConverter] = datetime.now(),
                    *users: discord.User):
        """
        Splits an amount between users and waits for reactions to clear the message
        :param amount: the amount of silver to split
        :param date: the date the split was on
        :param users: the mentions of users to split (as many as needed)
        """
        if amount <= 0:
            await ctx.send("Cannot have 0 or less silver")
            return
        date: datetime
        message = await ctx.send(f"{date.strftime('%m/%d')}\r"
                                 f"Splitting {amount} silver between {len(users)} members. "
                                 f"{floor(amount/len(users))} each.\r"
                                 f"React to this when you are paid or if you wish to donate.\r"
                                 f"{' '.join([str(user.mention) for user in users])}")
        self.tracked_messages.update({message.id: list(users)})

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if reaction.message.id in self.tracked_messages:
            if user in self.tracked_messages[reaction.message.id]:
                self.tracked_messages[reaction.message.id].remove(user)
                r: discord.Message
                r = reaction.message
                new_content = r.content.replace(user.mention, "", 1)
                if len(self.tracked_messages[r.id]) == 0:
                    await r.edit(content="All users paid! :smile:")
                else:
                    await r.edit(content=new_content)


def setup(bot: commands.Bot):
    bot.add_cog(GuildExtension(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("GuildExtension")
