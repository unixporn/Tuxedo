'''Information Cog'''

import traceback
import random
import discord
from discord.ext import commands


class Info:
    '''Information on various things the bot can see.'''

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['guild', 'discord'],
                      pass_context=True)
    async def server(self, ctx):
        '''Provides info on a server.'''

        server = ctx.message.server

        if ctx.message.channel.is_private:
            error_embed = discord.Embed(
                color=15746887,
                description='**Error**: \
                _Cannot be used in a DM._')
            await self.bot.say(embed=error_embed)
            return

        info_embed = discord.Embed()

        info_embed.set_author(
            name=server.name,
            icon_url=server.icon_url)

        if server.owner is None:
            server_owner = "**Error**: _Owner could not be found._"
        else:
            server_owner = server.owner.mention
            info_embed.color = server.owner.color

        info_embed.add_field(name="Owner", value=server_owner)
        info_embed.add_field(name="ID", value=server.id)
        info_embed.add_field(name="Created At", value=server.created_at)
        info_embed.add_field(name="Channels", value=len(server.channels))
        info_embed.add_field(name="Members", value=server.member_count)
        info_embed.add_field(name="Roles", value=len(server.roles))

        info_embed.add_field(
            name="Region",
            value=str(server.region).replace("-", " ").title())

        info_embed.add_field(
            name="AFK Timeout",
            value="{} Minutes".format(
                server.afk_timeout / 60).replace(".0", ""))

        info_embed.add_field(name="AFK Channel", value=server.afk_channel)

        info_embed.add_field(
            name="Verification Level",
            value=str(server.verification_level).title())

        if len(str(server.emojis)) < 1024 and server.emojis:
            emoji_str = " ".join([str(emoji) for emoji in server.emojis])
            info_embed.add_field(
                name="Emojis",
                value=emoji_str,
                inline=False)
        elif len(str(server.emojis)) >= 1024:
            emoji_list = random.sample(server.emojis, 10)
            emoji_str = "{} **+ {} More**".format(
                " ".join([str(emoji) for emoji in emoji_list]),
                len(server.emojis) - 10
            )
            info_embed.add_field(
                name="Emojis",
                value=emoji_str,
                inline=False)

        await ctx.send(embed=info_embed)

    @commands.command(name='channel',
                      aliases=['group', 'dm', 'pm', 'room'],
                      pass_context=True)
    async def _channelinfo(self, ctx, *, channel: discord.Channel=None):
        '''Provides info on a channel.'''

        if channel is None:
            channel = ctx.message.channel

        if channel.is_private:
            channel_topic = "Direct Message."
        if channel.topic is "" or channel.topic is None:
            channel_topic = "No Topic."
        else:
            channel_topic = channel.topic

        info_embed = discord.Embed(description="_{}_".format(channel_topic))

        if channel.is_private:
            info_embed.set_author(name="DM: {}".format(channel.user.name))
        else:
            info_embed.set_author(name="#{}".format(channel.name))

        info_embed.add_field(name="ID", value=channel.id)
        info_embed.add_field(name="Created At", value=channel.created_at)

        if not channel.is_private:
            info_embed.add_field(name="Default", value=channel.is_default)
            info_embed.add_field(name="Position", value=channel.position + 1)

        await self.bot.say(embed=info_embed)

    @info.command(name='role',
                  aliases=['title', 'tag', 'coloredbullshit'],
                  pass_context=True)
    async def _roleinfo(self, ctx, *, role: discord.Role=None):
        '''Provides info on a role.'''

        if ctx.message.channel.is_private:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: _Cannot be used in a DM._")
            await self.bot.say(embed=error_embed)
            return

        if role is None:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: _No role provided._")
            await self.bot.say(embed=error_embed)
            return

        info_embed = discord.Embed(color=role.color)

        info_embed.set_author(name="@{}".format(role.name))

        info_embed.add_field(name="ID", value=role.id)
        info_embed.add_field(name="Created At", value=role.created_at)

        if role.color.value is 0:
            role_color = "None"
        else:
            role_color = role.color
        info_embed.add_field(name="Color", value=role_color)

        info_embed.add_field(name="Displayed Separately", value=role.hoist)
        info_embed.add_field(name="Mentionable", value=role.mentionable)
        info_embed.add_field(name="Position", value=role.position)

        permissions_list = []
        for permission in iter(role.permissions):
            if permission[1]:
                permissions_list.append(permission[0])

        permissions_str = ", ".join(permissions_list).replace("_", " ").title()

        if len(permissions_str) >= 1000:
            info_embed.add_field(
                name="Permissions",
                value="***Error:***_Too many permissions._", inline=False)
        elif len(permissions_str) == 0:
            info_embed.add_field(name="Permissions",
                                 value="None", inline=False)
        else:
            info_embed.add_field(name="Permissions",
                                 value=permissions_str, inline=False)

        await self.bot.say(embed=info_embed)

    @info.command(name='user',
                  aliases=['person', 'account', 'member', 'muthafucka'],
                  pass_context=True)
    async def _userinfo(self, ctx, *, user: discord.Member=None):
        '''Provides info on a user.'''

        if user is None:
            user = ctx.message.author

        if ctx.message.channel.is_private:
            embed_color = discord.Color.default()
        else:
            embed_color = user.color

        info_embed = (discord.Embed(color=embed_color))
        info_embed.set_author(name="@{}#{}".format(
            user.name, user.discriminator))
        info_embed.set_thumbnail(url=user.avatar_url)
        info_embed.add_field(name="ID", value=user.id)
        info_embed.add_field(name="Created At", value=user.created_at)

        if not ctx.message.channel.is_private:
            info_embed.add_field(name="Joined At", value=user.joined_at)

            info_embed.add_field(name="Status", value=str(user.status).title())

            info_embed.add_field(name="Nickname", value=user.nick)

            if user.color.value is 0:
                user_color = "None"
            else:
                user_color = user.color
            info_embed.add_field(name="Color", value=user_color)

            info_embed.add_field(name="Game", value=user.game)

            role_list = ", ".join(role.name for role in user.roles[1:])
            if len(role_list) >= 500:
                info_embed.add_field(
                    name="Roles",
                    value="**Error:***_Too many roles._",
                    inline=False)
            elif len(role_list) == 0:
                info_embed.add_field(
                    name="Roles",
                    value="None",
                    inline=False)
            else:
                info_embed.add_field(
                    name="Roles",
                    value=role_list,
                    inline=False)

        await self.bot.say(embed=info_embed)

    @info.command(name='emoji',
                  aliases=['emote', 'facething'])
    async def _emojiinfo(self, *, emoji: discord.Emoji=None):
        '''Provides info on an emoji.'''

        if emoji is None:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error:** _No emoji provided._")
            await self.bot.say(embed=error_embed)
            return

        info_embed = discord.Embed()
        info_embed.set_author(name=":{}:".format(emoji.name))
        info_embed.set_thumbnail(url=emoji.url)

        info_embed.add_field(name="ID", value=emoji.id)
        info_embed.add_field(name="Server", value=emoji.server.name)
        info_embed.add_field(name="Created At", value=str(emoji.created_at))
        info_embed.add_field(name="Twitch Integrated", value=emoji.managed)

        await self.bot.say(embed=info_embed)

def setup(bot):
    '''Adds to d.py bot.'''
    bot.add_cog(Info(bot))
