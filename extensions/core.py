import discord
import os
from utils import permissions
from discord.ext import commands
import time
import asyncio
import sys
import cpuinfo
import math
import psutil

def propcheck(prop, d):
    return d[prop] if d[prop] else "None"

class Core:

    def __init__(self, bot):
        self.bot = bot
        self.color = "#000000"
        self.emoji = ":nut_and_bolt:"
        self.settings = {
            'extensions': []
        }

        @self.bot.check
        async def no_dms(ctx):
            return ctx.guild is not None
        self.init_extensions()

    def init_extensions(self):
        for ext in os.listdir('extensions'):
            if ext.endswith('.py') and not ext.startswith('core'):
                try:
                    self.bot.load_extension(f'extensions.{ext[:-3]}')
                    self.settings['extensions'].append(
                        f'extensions.{ext[:-3]}')
                except:
                    pass

    def humanbytes(self, B) -> str:  # function lifted from StackOverflow
        'Return the given bytes as a human friendly KB, MB, GB, or TB string'
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2)  # 1,048,576
        GB = float(KB ** 3)  # 1,073,741,824
        TB = float(KB ** 4)  # 1,099,511,627,776

        if B < KB:
            return '{0} {1}'.format(
                B, 'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B/KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B/MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B/GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B/TB)

    @commands.command(aliases=['bot', 'source', 'code', 'github'])
    async def about(self, ctx):
        text = """
```ini
upmo is a private instance of Erio by ry00001.
Our repo: https://github.com/unixporn/upmo-discord

[ Tuxedo ]
; An open-source moderation bot for Discord
; Made by ry00001 in Python 3.6 using Discord.py
; Source code freely available at https://github.com/ry00000/Erio
[ Credits ]
; HexadecimalPython: Original core
; Liara: eval
; Devoxin/Kromatic: Hosting and rewritten core, Lavalink.py that powers music!
[ Special thanks ]
; The people that made pull requests and contributed to the bot
; The entirety of Discord Bots
; LewisTehMinerz, for being awesome and hosting
; Liara, for being awesome in general
; Liz, for being a human rubber ducky for tempbans. (Rubber ducky debugging helps.)
; Ged, for also being awesome and hosting
; All my awesome users!
```
        """

        await ctx.send(text)

    @commands.command(aliases=['addbot', 'connect', 'join'],
                      hidden=True)
    async def invite(self, ctx):
        text = """
This bot is a private instance of Erio by ry00001.
It cannot be added to other servers.

Instead, add Erio to your server:
<https://discordapp.com/oauth2/authorize?client_id=338695256759599117&scope=bot>

It has most important features from upmo, including starboard and modlogs.
        """

        await ctx.send(text)

    @commands.command()
    async def stats(self, ctx):
        mem = psutil.virtual_memory()
        currproc = psutil.Process(os.getpid())
        total_ram = self.humanbytes(mem[0])
        available_ram = self.humanbytes(mem[1])
        usage = self.humanbytes(currproc.memory_info().rss)
        text = f"""
```
Total RAM: {total_ram}
Available RAM: {available_ram}
RAM used by bot: {usage}
Number of bot commands: {len(ctx.bot.commands)}
Number of extensions present: {len(ctx.bot.cogs)}
Number of users: {len(ctx.bot.users)}
```
"""
        await ctx.send(text)

    @commands.command(aliases=["le"], hidden=True)
    @permissions.owner()
    async def load(self, ctx, name: str):
        """ Load an extension into the bot """
        m = await ctx.send(f'Loading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name not in self.settings['extensions']:
            try:
                self.bot.load_extension(extension_name)
                self.settings['extensions'].append(extension_name)
                await m.edit(content='Extension loaded.')
            except Exception as e:
                await m.edit(
                    content=f'Error while loading {name}\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension already loaded.')

    @commands.command(aliases=["ule", "ul"], hidden=True)
    @permissions.owner()
    async def unload(self, ctx, name: str):
        """ Unload an extension from the bot """
        m = await ctx.send(f'Unloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            self.settings['extensions'].remove(extension_name)
            await m.edit(content='Extension unloaded.')
        else:
            await m.edit(content='Extension not found or not loaded.')

    @commands.command(aliases=["rle", "reloady", "rl"], hidden=True)
    @permissions.owner()
    async def reload(self, ctx, name: str):
        """ Reload an extension into the bot """
        m = await ctx.send(f'Reloading {name}')
        extension_name = 'extensions.{0}'.format(name)
        if extension_name in self.settings['extensions']:
            self.bot.unload_extension(extension_name)
            try:
                self.bot.load_extension(extension_name)
                await m.edit(content='Extension reloaded.')
            except Exception as e:
                self.settings['extensions'].remove(extension_name)
                await m.edit(
                    content=f'Failed to reload extension\n`{type(e).__name__}: {e}`')
        else:
            await m.edit(content='Extension isn\'t loaded.')

    @commands.command(aliases=["restart", 'die'], hidden=True)
    @permissions.owner()
    async def reboot(self, ctx):
        """ Ends the bot process """
        await ctx.send("Rebooting...")
        sys.exit(0)

    @commands.command(aliases=["logout", "shutdown"], hidden=True)
    @permissions.owner()
    async def logoff(self, ctx):
        """ Logs the bot off Discord """
        await ctx.send("Shutting down...")
        await self.bot.logout()

    @commands.command()
    async def ping(self, ctx):
        before = time.monotonic()
        pong = await ctx.send("...")
        after = time.monotonic()
        ping = (after - before) * 1000
        await pong.edit(content="`PING discordapp.com {}ms`".format(int(ping)))

    # Ported from rybot
    @commands.command(description="Manage those prefixes.", hidden=True)
    async def prefix(self, ctx, method: str, *, prefix: str=None):
        if method == "add":
            if not permissions.is_owner_check(ctx):
                return await ctx.send(
                    ':no_entry_sign: You do not have permission to use this command.')
            prefix = prefix.strip("\"")
            prefix = prefix.strip('\'')
            if prefix is None:
                return await ctx.send("Specify a prefix to add.")
            if prefix in self.bot.prefix:
                return await ctx.send("Duplicate prefixes are not allowed!")
            self.bot.prefix.append(prefix)
            await ctx.send("Added prefix `" + prefix + "`")
        elif method == "remove":
            if not permissions.is_owner_check(ctx):
                return await ctx.send(
                    ':no_entry_sign: You do not have permission to use this command.')
            prefix = prefix.strip("\"")
            prefix = prefix.strip('\'')
            if prefix is None:
                return await ctx.send("Specify a prefix to remove.")
            if prefix not in self.bot.prefix:
                return await ctx.send("The specified prefix is not in use.")
            self.bot.prefix.remove(prefix)
            await ctx.send("Removed prefix `" + prefix + "`")
        elif method == "list":  # Tuxedo Exclusive Feature™
            prefixes = "\n".join(self.bot.prefix)
            await ctx.send(f"```\n{prefixes}```")
        else:
            await ctx.send('Method needs to be `add`, `remove`, `list`.')

    @commands.command(hidden=True)
    @permissions.owner()
    async def error(self, ctx):
        3 / 0

    @commands.command(hidden=True)
    @permissions.owner()
    async def alias(self, ctx, _from, to):
        _from = _from.replace('\'', '').replace('"', '')
        to = to.replace('\'', '').replace('"', '')
        fromcmd = self.bot.get_command(_from)
        if _from == to:
            return await ctx.send(
                ':x: You cannot register an alias with the same name as the command.')
        if fromcmd == None:
            return await ctx.send(
                ':x: The command that needs to be registered is invalid.')
        if to in self.bot.all_commands:
            return await ctx.send(
                ':x: The command to register is already a thing.')
        self.bot.all_commands[to] = fromcmd
        await ctx.send(
            ':ok_hand: Registered. Or at least I hope. This command is in beta and probably buggy. It may not work.')


def setup(bot):
    bot.add_cog(Core(bot))
