import re
from datetime import datetime
from typing import List, Iterator, Optional

import discord
from dateutil.tz import gettz
from discord.ext import commands

from NoConflictCog import NoConflictCog
from SpecialChecks import EventCheck


class TimeExtension(NoConflictCog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.watched_channels: List[discord.ChannelType] = []
        self.formats: List[re.Pattern] = [
            re.compile(r"(?P<hour>\d{1,2}):(?P<minute>\d{2}).*UTC")
        ]
        self.timezones = ["America/Los_Angeles", "America/Denver", "America/New_York", "Europe/Berlin",
                          "America/Chicago"]
        self.converted_messages: List[int] = []

    def __unconverted_message(self, message: discord.Message, *args) -> bool:
        return message.id not in self.converted_messages

    def __watched_channel(self, message: discord.Message, *args) -> bool:
        return message.channel in self.watched_channels

    def __not_self(self, message: discord.Message, *args) -> bool:
        return message.author.id != self.bot.user.id

    @commands.command()
    async def add_pattern(self, ctx: commands.Context, pattern: re.compile):
        """
        Add a regex pattern for recognizing dates within a string
        :param pattern:
        """
        self.formats.append(pattern)
        await ctx.send(f"Now watching pattern {str(pattern)}")

    @commands.command()
    async def remove_pattern(self, ctx: commands.Context, pattern_number: Optional[int], pattern: Optional[re.compile]):
        if pattern_number and len(self.formats) > pattern_number > 0 and not pattern:
            pattern = self.formats.pop(pattern_number)
            await ctx.send(f"Removed pattern: {str(pattern.pattern)}")
        elif not pattern_number and pattern in self.formats:
            self.formats.remove(pattern)
            await ctx.send(f"Removed {pattern.pattern}")
        else:
            await ctx.send("Could not remove pattern")

    @commands.command()
    async def watch_channel(self, ctx: commands.Context):
        self.watched_channels.append(ctx.channel)
        await ctx.send("Channel is now being watched")

    @commands.command()
    async def unwatch_channel(self, ctx: commands.Context):
        if ctx.channel in self.watched_channels:
            self.watched_channels.remove(ctx.channel)
            await ctx.send("This channel is no longer being watched")
        else:
            await ctx.send("This channel is not currently being watched")

    @commands.command()
    async def add_timezone(self, ctx: commands.Context, timezone: str):
        if gettz(timezone) is None:
            await ctx.send("That timezone does not exist, please try again with the full timezone name supplied "
                           "(Ex. America/New_York)"
                           "or it is in UTC offset form (E.x UTC-4).")
        await ctx.send(f"Timezone {timezone} added.")
        self.timezones.append(timezone)

    @commands.command()
    async def remove_timezone(self, ctx: commands.Context, timezone: str):
        if timezone in self.timezones:
            self.timezones.remove(timezone)
            await ctx.send(f"Timezone {timezone} added.")
        else:
            await ctx.send(f"Timezone {timezone} does not exist in bot.")

    @commands.Cog.listener()
    @EventCheck(__unconverted_message)
    @EventCheck(__not_self)
    @EventCheck(__watched_channel)
    async def on_message(self, message: discord.Message):
        link = "https://savvytime.com/countdown?name=Countdown"
        ret = ""
        f: re.Pattern
        formatted: Iterator[Optional[re.Match]] = map(lambda f: f.search(message.content), self.formats)
        formatted = list(filter(lambda x: x is not None, formatted))
        if formatted:
            longest_match: re.Match = max(formatted, key=lambda x: len(x.group(0)))
            time = datetime.now()
            match_dict = longest_match.groupdict()
            time = datetime(
                int(match_dict.get("year", time.year)),
                int(match_dict.get("month", time.month)),
                int(match_dict.get("day", time.day)),
                hour=int(match_dict.get("hour", time.hour)),
                minute=int(match_dict.get("minute", time.minute)),
                tzinfo=gettz("UTC")
            )
            ret = "Event happening at " + time.strftime("%I:%M %p UTC") + "\r"
            for timezone in self.timezones:
                newtime = gettz(timezone)
                newtime = time.astimezone(newtime)
                ret += newtime.strftime("%I:%M %p %Z") + "\r"
            self.converted_messages.append(message.id)
            ret += f"Countdown here: "
            await message.channel.send(
                ret,
                embed=discord.Embed(
                    title="Click here for coundown",
                    url=f"{link+'&time='+str(int(time.timestamp()*1000))}"
                )
            )


def setup(bot: commands.Bot):
    bot.add_cog(TimeExtension(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("TimeExtension")
