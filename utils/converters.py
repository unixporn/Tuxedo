from discord.ext import commands
from discord.ext.commands.errors import BadArgument
import emoji
import asyncio


class EmojiStrConverter(commands.Converter):
    """Converts to a :class:`Union[discord.Emoji, str]`."""
    @asyncio.coroutine
    def convert(self, ctx, argument):
        try:
            return commands.EmojiConverter.convert(ctx, argument)
        except BadArgument:
            try:
                return emoji.emojize(f"{argument}")
            except:  # XXX What error?
                raise BadArgument(f'Emoji "{argument}" not found.')
