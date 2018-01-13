# -*- coding: utf-8 -*-

# upmo - custom bot for the /r/unixporn discord server
# Ready to rice?
# main.py, utils, and core.py copyright (c) Tuxedo Team 2017
# Used and modified with permission
# All original work by ry00001 and taciturasa.

'''Main File'''

import traceback
import json
import rethinkdb as r
import sys
import discord
from discord.ext import commands
from discord.ext.commands import errors as commands_errors
from discord import utils as dutils
from utils import permissions

# INITIALIZE BOT #


class Bot(commands.Bot):
    '''Custom Bot Class that overrides the commands.ext one'''

    def __init__(self, **options):
        super().__init__(self.get_prefix_new, **options)
        print('Performing initialization...\n')
        self.cmd_help = cmd_help
        with open('config.json') as f:
            self.config = json.load(f)
            self.prefix = self.config.get('BOT_PREFIX')
            self.version = self.config.get('VERSION')
            self.integrations = self.config.get('INTEGRATIONS')
            self.maintenance = self.config.get('MAINTENANCE')
            self.directrooms = self.config.get('DIRECTROOMS')
        self.remove_command("help")
        self.rdb = self.config['RETHINKDB']['DB']
        self.rtables = ["settings", "starboard", "modlog", "tempbans"]
        self.init_rethinkdb()
        print('Initialization complete.\n\n')

    async def get_prefix_new(self, bot, msg):
        return commands.when_mentioned_or(*self.prefix)(bot, msg)

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        await self.change_presence(
            game=discord.Game(
                name=f'{self.prefix[0]}help',
                type=2))
        self.load_extension('extensions.core')

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.id in self.config.get('BLOCKED'):
            return
        if (not permissions.owner_id_check(self, str(message.author.id))
                and self.maintenance):
            return
        await self.process_commands(message)

    def init_rethinkdb(self):
        print('Now initialising RethinkDB...')
        dbc = self.config['RETHINKDB']

        try:
            self.conn = r.connect(
                host=dbc['HOST'],
                port=dbc['PORT'],
                db=dbc['DB'],
                user=dbc['USERNAME'],
                password=dbc['PASSWORD'])

            dbs = r.db_list().run(self.conn)
            if self.rdb not in dbs:
                print('Database not present. Creating...')
                r.db_create(self.rdb).run(self.conn)
            tables = r.db(self.rdb).table_list().run(self.conn)
            for i in self.rtables:
                if i not in tables:
                    print(f'Table {i} not found. Creating...')
                    r.table_create(i).run(self.conn)

        except Exception as e:
            print('RethinkDB init error!\n{}: {}'.format(type(e).__name__, e))
            sys.exit(1)
        print('RethinkDB initialisation successful.')

    def find_command(self, cmdname: str):
        for i in self.commands:
            if i.name == cmdname:
                return i
        return False


async def cmd_help(ctx):
    if ctx.invoked_subcommand:
        _help = await ctx.bot.formatter.format_help_for(
            ctx, ctx.invoked_subcommand)
    else:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)
    for page in _help:
        await ctx.send(page)

bot = Bot()
print("bot created.\n")

# INITIALIZE BOT END #


@bot.listen("on_command_error")
async def on_command_error(ctx, error):
    if isinstance(error, commands_errors.MissingRequiredArgument):
        await cmd_help(ctx)

    elif isinstance(error, commands_errors.CommandInvokeError):
        error = error.original
        _traceback = traceback.format_tb(error.__traceback__)
        _traceback = ''.join(_traceback)
        embed_fallback = "**ERROR: <@97788939196182528>**"

        error_embed = discord.Embed(
            title="An error has occurred.",
            color=0xFF0000,
            description=(
                "This is (probably) a bug. This has been automatically "
                "reported, but give <@97788939196182528> a heads-up in DMs.")
        )

        error_embed.add_field(
            name="`{}` in command `{}`".format(
                type(error).__name__, ctx.command.qualified_name),
            value=(
                "```py\nTraceback (most recent call last):"
                "\n{}{}: {}```").format(
                    _traceback,
                    type(error).__name__,
                    error))

        await ctx.send(embed_fallback, embed=error_embed)

    elif isinstance(error, commands_errors.CommandOnCooldown):
        await ctx.send(
            'This command is on cooldown. You can use this command in '
            '`{0:.2f}` seconds.'.format(
                error.retry_after))
    else:
        ctx.send(error)


@bot.command(aliases=['instructions'])
async def help(ctx, command: str=None):
    cmd = ctx.bot.find_command(command)
    helptext = await ctx.bot.formatter.format_help_for(
        ctx, cmd if cmd is not False else ctx.bot)
    helptext = helptext[0]
    try:
        await ctx.author.send(helptext)
        await ctx.message.add_reaction("📬")
    except discord.Forbidden:
        await ctx.send(helptext)
bot.get_command("help").hidden = True

print("Connecting...")
bot.run(bot.config['BOT_TOKEN'])
