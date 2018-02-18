import random
import discord
from discord.ext import commands
from discord import utils as dutils
from typing import Union

class Info:
    'Information on various things the bot can see.'

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def info(self, ctx, object):
        """Automatically selects approproiate info command."""
        ...

    @commands.command(aliases=['guild', 'discord'])
    async def server(self, ctx):
        """Provides info on a server."""
        guild = ctx.guild
        e = discord.Embed()
        e.set_author(name=guild.name, icon_url=guild.icon_url)
        if guild.owner is None:
            guild_owner = '**Error**: _Owner could not be found._'
        else:
            guild_owner = guild.owner.mention
            e.color = guild.owner.color
        e.add_field(name='Owner', value=guild_owner)
        e.add_field(name='ID', value=guild.id)
        e.add_field(name='Created At', value=guild.created_at)
        e.add_field(name='Channels', value=len(guild.channels))
        e.add_field(name='Members', value=guild.member_count)
        e.add_field(name='Roles', value=len(guild.roles))
        e.add_field(
            name='Region',
            value=str(guild.region).replace('-', ' ').title())
        e.add_field(
            name='AFK Timeout',
            value='{} Minutes'.format(
                guild.afk_timeout / 60).replace('.0', ''))
        e.add_field(
            name='AFK Channel',
            value=guild.afk_channel)
        e.add_field(
            name='Verification Level',
            value=str(guild.verification_level).title())
        if guild.emojis:
            if (len(guild.emojis) <= 10):
                emoji_str = ' '.join([str(emoji) for emoji in guild.emojis])
                e.add_field(name='Emojis', value=emoji_str, inline=False)
            else:
                emoji_list = random.sample(guild.emojis, 10)
                emoji_str = '{} **+ {} More**'.format(
                    ' '.join([str(emoji) for emoji in emoji_list]),
                            len(guild.emojis) - 10)
                e.add_field(name='Emojis', value=emoji_str, inline=False)
        await ctx.send(embed=e)

    @commands.command(name='channel', aliases=['group', 'dm', 'pm', 'room'])
    async def channel(self, ctx, *, channel=None):
        """Provides info on a channel."""

        if channel is None:
            channel = ctx.channel
        elif channel.startswith('<#'):
            channel = channel.replace('<#', '')
            channel = channel.replace('>', '')
            channel = self.bot.get_channel(int(channel))
        else:
            channel = dutils.get(
                ctx.message.guild.channels,
                name=channel)
            if channel is None:
                await ctx.send(":x: Channel not found.", delete_after=3)
                return

        if isinstance(channel, discord.VoiceChannel):
            description = f"_{len(channel.members)} Connected._"
            name = channel.name
        elif isinstance(channel, discord.CategoryChannel):
            description = f"_Holds {len(channel.channels)} channels._"
            name = channel.name
        else:
            description = f"_{channel.topic}_"
            name = f"#{channel.name}"
        e = discord.Embed(description=description)
        e.set_author(name=name)
        e.add_field(name="ID", value=channel.id)
        e.add_field(name="Created At", value=channel.created_at)
        e.add_field(name="Position", value=channel.position + 1)

        await ctx.send(embed=e)

    @commands.command(aliases=['title', 'tag'], pass_context=True)
    async def role(self, ctx, *, role: discord.Role=None):
        """Provides info on a role."""
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            await ctx.send(':x: Cannot be used in a DM.', delete_after=3)
            return
        if role is None:
            await ctx.send(':x: No role provided.', delete_after=3)
            return
        e = discord.Embed(color=role.color)
        e.set_author(name='@{}'.format(role.name))
        e.add_field(name='ID', value=role.id)
        e.add_field(name='Created At', value=role.created_at)
        if role.color.value is 0:
            role_color = 'None'
        else:
            role_color = role.color
        e.add_field(name='Color', value=role_color)
        e.add_field(name='Displayed Separately', value=role.hoist)
        e.add_field(name='Mentionable', value=role.mentionable)
        e.add_field(name='Position', value=role.position)
        permissions_list = []
        for permission in iter(role.permissions):
            if permission[1]:
                permissions_list.append(permission[0])
        permissions_str = ', '.join(permissions_list).replace('_', ' ').title()
        if len(permissions_str) >= 1000:
            e.add_field(
                name='Permissions',
                value='***Error:***_Too many permissions._',
                inline=False)
        elif len(permissions_str) == 0:
            e.add_field(name='Permissions', value='None', inline=False)
        else:
            e.add_field(
                name='Permissions', value=permissions_str, inline=False)
        await ctx.send(embed=e)

    @commands.command(name='user', aliases=['person', 'account', 'member'])
    async def user(self, ctx, *, user: discord.Member=None):
        """Provides info on a user."""
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            await ctx.send(':x: Cannot be used in a DM.', delete_after=3)
            return
        if user is None:
            user = ctx.author
        embed_color = user.color
        e = discord.Embed(color=embed_color)
        e.set_author(name='@{}#{}'.format(user.name, user.discriminator))
        e.set_thumbnail(url=user.avatar_url)
        e.add_field(name='ID', value=user.id)
        e.add_field(name='Created At', value=user.created_at)
        e.add_field(name='Joined At', value=user.joined_at)
        e.add_field(name='Status', value=str(user.status).title())
        e.add_field(name='Nickname', value=user.nick)
        if user.color.value is 0:
            user_color = 'None'
        else:
            user_color = user.color
        e.add_field(name='Color', value=user_color)
        e.add_field(name='Game', value=user.game)
        role_list = ', '.join((role.name for role in user.roles[1:]))
        if len(role_list) >= 1024:
            e.add_field(
                name='Roles',
                value='**Error:***_Too many roles._',
                inline=False)
        elif len(role_list) == 0:
            e.add_field(name='Roles', value='None', inline=False)
        else:
            e.add_field(name='Roles', value=role_list, inline=False)
        await ctx.send(embed=e)


def setup(bot):
    """Adds to d.py bot. Necessary for all cogs."""
    bot.add_cog(Info(bot))
