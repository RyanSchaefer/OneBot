import re
from datetime import datetime
from typing import List, Iterator, Optional

import discord
from dateutil.tz import gettz
from discord.ext import commands

from NoConflictCog import NoConflictCog
from SpecialChecks import EventCheck, EventCheckAny
from AdminCommands import AdminCommands


class TimeExtension(NoConflictCog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.watched_channels: List[discord.ChannelType] = []
        self.watched_users: List[discord.abc.User] = []
        self.formats: List[re.Pattern] = [
            re.compile(r"(?#Default pattern for matching just a time)"
                       r"(?P<hour>\d{1,2}):(?P<minute>\d{2}) ?(?P<tz>[\w/]+)"),
            re.compile(
                r"(?#Default pattern for matching a date and a time)"
                r"(?P<hour>[0-2]?[0-4]):(?P<minute>[0-5][0-9]) ?"
                r"(?P<tz>[\w/]+) "
                r"(?P<month>(?:0?[1-9]|1[012]))/(?P<day>(?:0[0-9]|2[0-9]|3[0-1]))"
            )
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

    def __check_user(self, message: discord.Message, *args) -> bool:
        return message.author in self.watched_users

    @commands.command()
    async def add_pattern(self, ctx: commands.Context, pattern: re.compile):
        """
        Add a regex pattern for recognizing dates within a string
        :param pattern: the pattern to match, when there are multiple conflicting patterns only the longest match will
        be kept.
        The pattern should define any number groups with the name ?P<minute>, ?P<hour>, ?P<day>, ?P<month>, ?P<year>,
        ?P<tz> to denote how to convert the string to a usable datetime.
        It is recommended you use a site like regex101.com before adding a pattern
        """
        self.formats.append(pattern)
        await ctx.send(f"Now watching pattern {str(pattern)}")

    @commands.command()
    async def remove_pattern(self, ctx: commands.Context, pattern_number: Optional[int], pattern: Optional[re.compile]):
        """
        Remove a regex pattern
        :param pattern_number: Optional, if an int is specified then that pattern will be removed (0 indexed, based on
        return of $patterns)
        :param pattern: Optional, A pattern to remove
        """
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
        """
        When called in a channel, that channel will be added to the watchlist for time conversions
        """
        self.watched_channels.append(ctx.channel)
        await ctx.send("Channel is now being watched")

    @commands.command()
    async def unwatch_channel(self, ctx: commands.Context):
        """
        When called in a channel, that channel will be removed from the watchlist for time conversions
        """
        if ctx.channel in self.watched_channels:
            self.watched_channels.remove(ctx.channel)
            await ctx.send("This channel is no longer being watched")
        else:
            await ctx.send("This channel is not currently being watched")

    @commands.command()
    async def add_timezone(self, ctx: commands.Context, timezone: str):
        """
        Add a timezone to the list of conversions for each message, must be in IANA timezone database as a
        canonical timezone or in ISO UTC format (UTC[+-]# or UTC[+-]####)
        :param timezone: The valid timezone string
        """
        if gettz(timezone) is None:
            await ctx.send("That timezone does not exist, please try again with the full timezone name supplied "
                           "(Ex. America/New_York)"
                           "or it is in UTC offset form (E.x UTC-4).")
        await ctx.send(f"Timezone {timezone} added.")
        self.timezones.append(timezone)

    @commands.command()
    async def remove_timezone(self, ctx: commands.Context, timezone: str):
        """
        Remove a previously added timezone
        :param timezone:
        """
        if timezone in self.timezones:
            self.timezones.remove(timezone)
            await ctx.send(f"Timezone {timezone} added.")
        else:
            await ctx.send(f"Timezone {timezone} does not exist in bot.")

    @commands.command()
    async def patterns(self, ctx: commands.context):
        await ctx.send("\r\r".join(map(lambda x: x.pattern, self.formats)))

    @commands.Cog.listener()
    @EventCheck(__unconverted_message)
    @EventCheck(__not_self)
    @EventCheckAny(__watched_channel, __check_user)
    async def on_message(self, message: discord.Message):
        link = "https://savvytime.com/countdown?name=Countdown"
        ret = ""
        f: re.Pattern
        formatted: Iterator[Optional[re.Match]] = map(lambda f: f.search(message.content), self.formats)
        formatted = list(filter(lambda x: x is not None, formatted))
        embed = discord.Embed()
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
                tzinfo=gettz(match_dict.get("tz", "UTC"))
            )
            ret = "Event happening at " + time.strftime("%I:%M %p %Z") + "\r"
            for timezone in self.timezones:
                newtime = gettz(timezone)
                newtime = time.astimezone(newtime)
                embed.add_field(name=newtime.strftime("%Z"), value=newtime.strftime("%I:%M %p"))
                ret += newtime.strftime("%I:%M %p %Z") + "\r"
            self.converted_messages.append(message.id)
            embed.title = "Click here for countdown"
            embed.url = f"{link+'&time='+str(int(time.timestamp()*1000))}"
            await message.channel.send(
                embed=embed
            )


def setup(bot: commands.Bot):
    bot.add_cog(TimeExtension(bot))


def teardown(bot: commands.Bot):
    bot.remove_cog("TimeExtension")
