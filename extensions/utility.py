import discord
from discord.ext import commands
from utils import permissions, randomness
import aiohttp
import asyncio
import subprocess
import inspect
import collections
import traceback
import io
import datetime
import time
from contextlib import redirect_stdout
from lxml import etree
import textwrap
import rethinkdb as r
from urllib.parse import quote as uriquote
from typing import Union


class Utility:

    def __init__(self, bot):
        self.bot = bot
        self.repl_sessions = {}
        self.repl_embeds = {}
        self.aioclient = aiohttp.ClientSession()
        self.conn = bot.conn
        self._eval = {}

    def cleanup_code(self, content):
        '''Automatically removes code blocks from the code.'''
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    def get_syntax_error(self, err):
        '''Returns SyntaxError formatted for repl reply.'''
        return '```py\n{0.text}{1:>{0.offset}}\n{2}: {0}```'.format(
            err,
            '^',
            type(err).__name__)

    async def post_to_hastebin(self, string):
        '''Posts a string to hastebin.'''
        url = "https://hastebin.com/documents"
        data = string.encode('utf-8')
        async with self.aioclient.post(url=url, data=data) as haste_response:
            haste_key = (await haste_response.json())['key']
            haste_url = f"http://hastebin.com/{haste_key}"
        # data = {'sprunge': ''}
        # data['sprunge'] = string
        # haste_url = await self.aioclient.post(url='http://sprunge.us',
        # data=data)
        return haste_url

    @commands.group(name='shell',
                    aliases=['ipython', 'repl',
                             'longexec', 'core', 'overkill'],
                    pass_context=True,
                    invoke_without_command=True)
    @permissions.owner()
    async def repl(self, ctx, *, name: str=None):
        '''Head on impact with an interactive python shell.'''
        # TODO Minimize local variables
        # TODO Minimize branches

        session = ctx.message.channel.id

        embed = discord.Embed(
            description="_Enter code to execute or evaluate. "
            "`exit()` or `quit` to exit._",
            timestamp=datetime.datetime.now())

        embed.set_footer(
            text="Interactive Python Shell",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb"
            "/c/c3/Python-logo-notext.svg/1024px-Python-logo-notext.svg.png")

        if name is not None:
            embed.title = name.strip(" ")

        history = collections.OrderedDict()

        variables = {
            'ctx': ctx,
            'bot': self.bot,
            'message': ctx.message,
            'server': ctx.message.guild,
            'channel': ctx.message.channel,
            'author': ctx.message.author,
            'discord': discord,
            'r': r,
            'conn': self.conn,
            '_': None
        }

        if session in self.repl_sessions:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: "
                "_Shell is already running in channel._")
            await ctx.send(embed=error_embed)
            return

        shell = await ctx.send(embed=embed)

        self.repl_sessions[session] = shell
        self.repl_embeds[shell] = embed

        while True:
            response = await self.bot.wait_for(
                'message',
                check=lambda m: m.content.startswith('`') and m.author == ctx.author and m.channel == ctx.channel)

            cleaned = self.cleanup_code(response.content)
            shell = self.repl_sessions[session]

            # Regular Bot Method
            try:
                await ctx.message.channel.get_message(
                    self.repl_sessions[session].id)
            except discord.NotFound:
                new_shell = await ctx.send(embed=self.repl_embeds[shell])
                self.repl_sessions[session] = new_shell

                embed = self.repl_embeds[shell]
                del self.repl_embeds[shell]
                self.repl_embeds[new_shell] = embed

                shell = self.repl_sessions[session]

            try:
                await response.delete()
            except discord.Forbidden:
                pass

            if len(self.repl_embeds[shell].fields) >= 7:
                self.repl_embeds[shell].remove_field(0)

            if cleaned in ('quit', 'exit', 'exit()'):
                self.repl_embeds[shell].color = 16426522

                if self.repl_embeds[shell].title is not discord.Embed.Empty:
                    history_string = "History for {}\n\n\n".format(
                        self.repl_embeds[shell].title)
                else:
                    history_string = "History for latest session\n\n\n"

                for item in history.keys():
                    history_string += ">>> {}\n{}\n\n".format(
                        item,
                        history[item])

                haste_url = await self.post_to_hastebin(history_string)
                return_msg = "[`Leaving shell session. "\
                    "History hosted on hastebin.`]({})".format(
                        haste_url)

                self.repl_embeds[shell].add_field(
                    name="`>>> {}`".format(cleaned),
                    value=return_msg,
                    inline=False)

                await self.repl_sessions[session].edit(
                    embed=self.repl_embeds[shell])

                del self.repl_embeds[shell]
                del self.repl_sessions[session]
                return

            executor = exec
            if cleaned.count('\n') == 0:
                # single statement, potentially 'eval'
                try:
                    code = compile(cleaned, '<repl session>', 'eval')
                except SyntaxError:
                    pass
                else:
                    executor = eval

            if executor is exec:
                try:
                    code = compile(cleaned, '<repl session>', 'exec')
                except SyntaxError as err:
                    self.repl_embeds[shell].color = 15746887

                    return_msg = self.get_syntax_error(err)

                    history[cleaned] = return_msg

                    if len(cleaned) > 800:
                        cleaned = "<Too big to be printed>"
                    if len(return_msg) > 800:
                        haste_url = await self.post_to_hastebin(return_msg)
                        return_msg = "[`SyntaxError too big to be printed. "\
                            "Hosted on hastebin.`]({})".format(
                                haste_url)

                    self.repl_embeds[shell].add_field(
                        name="`>>> {}`".format(cleaned),
                        value=return_msg,
                        inline=False)

                    await self.repl_sessions[session].edit(
                        embed=self.repl_embeds[shell])
                    continue

            variables['message'] = response

            fmt = None
            stdout = io.StringIO()

            try:
                with redirect_stdout(stdout):
                    result = executor(code, variables)
                    if inspect.isawaitable(result):
                        result = await result
            except Exception as err:
                self.repl_embeds[shell].color = 15746887
                value = stdout.getvalue()
                fmt = '```py\n{}{}\n```'.format(
                    value,
                    traceback.format_exc())
            else:
                self.repl_embeds[shell].color = 4437377

                value = stdout.getvalue()

                if result is not None:
                    fmt = '```py\n{}{}\n```'.format(
                        value,
                        result)

                    variables['_'] = result
                elif value:
                    fmt = '```py\n{}\n```'.format(value)

            history[cleaned] = fmt

            print("got this far as well")
            if len(cleaned) > 800:
                cleaned = "<Too big to be printed>"

            try:
                if fmt is not None:
                    if len(fmt) >= 800:
                        haste_url = await self.post_to_hastebin(fmt)
                        self.repl_embeds[shell].add_field(
                            name="`>>> {}`".format(cleaned),
                            value="[`Content too big to be printed. "
                            "Hosted on hastebin.`]({})".format(
                                haste_url),
                            inline=False)

                        await self.repl_sessions[session].edit(
                            embed=self.repl_embeds[shell])
                    else:
                        self.repl_embeds[shell].add_field(
                            name="`>>> {}`".format(cleaned),
                            value=fmt,
                            inline=False)

                        await self.repl_sessions[session].edit(
                            embed=self.repl_embeds[shell])
                else:
                    self.repl_embeds[shell].add_field(
                        name="`>>> {}`".format(cleaned),
                        value="`Empty response, assumed successful.`",
                        inline=False)

                    await self.repl_sessions[session].edit(
                        embed=self.repl_embeds[shell])

            except discord.Forbidden:
                pass

            except discord.HTTPException as err:
                error_embed = discord.Embed(
                    color=15746887,
                    description='**Error**: _{}_'.format(err))
                await ctx.send(embed=error_embed)

    @repl.command(name='jump',
                  aliases=['hop', 'pull', 'recenter', 'whereditgo'],
                  pass_context=True)
    @permissions.owner()
    async def _repljump(self, ctx):
        '''Brings the shell back down so you can see it again.'''

        session = ctx.message.channel.id

        if session not in self.repl_sessions:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: _No shell running in channel._")
            await ctx.send(embed=error_embed)
            return

        shell = self.repl_sessions[session]
        embed = self.repl_embeds[shell]

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        try:
            await shell.delete()
        except discord.errors.NotFound:
            pass
        new_shell = await ctx.send(embed=embed)

        self.repl_sessions[session] = new_shell

        del self.repl_embeds[shell]
        self.repl_embeds[new_shell] = embed

    @repl.command(name='clear',
                  aliases=['clean', 'purge', 'cleanup',
                           'ohfuckme', 'deletthis'],
                  pass_context=True)
    @permissions.owner()
    async def _replclear(self, ctx):
        '''Clears the fields of the shell and resets the color.'''

        session = ctx.message.channel.id

        if session not in self.repl_sessions:
            error_embed = discord.Embed(
                color=15746887,
                description="**Error**: _No shell running in channel._")
            await ctx.send(embed=error_embed)
            return

        shell = self.repl_sessions[session]

        self.repl_embeds[shell].color = discord.Color.default()
        self.repl_embeds[shell].clear_fields()

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        await shell.edit(embed=self.repl_embeds[shell])

    @commands.command(name="announce")
    @permissions.owner()
    async def global_announce(self, ctx, content: str):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    await channel.send(
                        content=content)
                    break

    @commands.command(name="setavy")
    @permissions.owner()
    async def set_avy(self, ctx, *, avy: str):
        async with aiohttp.ClientSession() as sesh:
            async with sesh.get(avy) as r:
                await self.bot.user.edit(avatar=await r.read())
                await ctx.send(":ok_hand:")

    @commands.command(name='eval',
                      aliases=["ev", "e"])
    @permissions.owner()
    async def eval_cmd(self, ctx, *, code: str):
        """Evaluates Python code"""
        if self._eval.get('env') is None:
            self._eval['env'] = {}
        if self._eval.get('count') is None:
            self._eval['count'] = 0

        codebyspace = code.split(" ")
        print(codebyspace)
        silent = False
        if codebyspace[0] == "--silent" or codebyspace[0] == "-s":
            silent = True
            codebyspace = codebyspace[1:]
            code = " ".join(codebyspace)

        self._eval['env'].update({
            'self': self.bot,
            'ctx': ctx,
            'message': ctx.message,
            'channel': ctx.message.channel,
            'guild': ctx.message.guild,
            'author': ctx.message.author,
        })

        # let's make this safe to work with
        code = code.replace('```py\n', '').replace('```', '').replace('`', '')

        _code = (
            'async def func(self):\n  try:\n{}\n  '
            'finally:\n    self._eval[\'env\'].update(locals())').format(
                textwrap.indent(code, '    '))

        before = time.monotonic()
        # noinspection PyBroadException
        try:
            exec(_code, self._eval['env'])
            func = self._eval['env']['func']
            output = await func(self)

            if output is not None:
                output = repr(output)
        except Exception as e:
            output = '{}: {}'.format(type(e).__name__, e)
        after = time.monotonic()
        self._eval['count'] += 1
        count = self._eval['count']

        code = code.split('\n')
        if len(code) == 1:
            _in = 'In [{}]: {}'.format(count, code[0])
        else:
            _first_line = code[0]
            _rest = code[1:]
            _rest = '\n'.join(_rest)
            _countlen = len(str(count)) + 2
            _rest = textwrap.indent(_rest, '...: ')
            _rest = textwrap.indent(_rest, ' ' * _countlen)
            _in = 'In [{}]: {}\n{}'.format(count, _first_line, _rest)

        message = '```py\n{}'.format(_in)
        if output is not None:
            message += '\nOut[{}]: {}'.format(count, output)
        ms = int(round((after - before) * 1000))
        if ms > 100:  # noticeable delay
            message += '\n# {} ms\n```'.format(ms)
        else:
            message += '\n```'

        try:
            if ctx.author.id == self.bot.user.id:
                await ctx.message.edit(content=message)
            else:
                if not silent:
                    await ctx.send(message)
        except discord.HTTPException:
            if not silent:
                with aiohttp.ClientSession() as sesh:
                    async with sesh.post(
                            "https://hastebin.com/documents/",
                            data=output,
                            headers={"Content-Type": "text/plain"}) as r:
                        r = await r.json()
                        embed = discord.Embed(
                            description=(
                                "[View output - click]"
                                "(https://hastebin.com/raw/{})").format(
                                    r["key"]),
                            color=randomness.random_colour())
                        await ctx.send(embed=embed)

    @commands.command(aliases=['sys', 's', 'run', 'sh'],
                      description="Run system commands.")
    @permissions.owner()
    async def system(self, ctx, *, command: str):
        'Run system commands.'
        message = await ctx.send('<a:typing:401162479041773568> Processing...')
        result = []
        try:
            process = subprocess.Popen(command.split(
                ' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = process.communicate()
        except FileNotFoundError:
            stderr = f'Command not found: {command}'
        embed = discord.Embed(
            title="Command output",
            color=randomness.random_colour()
        )
        if len(result) >= 1 and result[0] in [None, b'']:
            stdout = 'No output.'
        if len(result) >= 2 and result[0] in [None, b'']:
            stderr = 'No output.'
        if len(result) >= 1 and result[0] not in [None, b'']:
            stdout = result[0].decode('utf-8')
        if len(result) >= 2 and result[1] not in [None, b'']:
            stderr = result[1].decode('utf-8')
        string = ""
        if len(result) >= 1:
            if (len(result[0]) >= 1024):
                stdout = result[0].decode('utf-8')
                string = string + f'[[STDOUT]]\n{stdout}'
                link = await self.post_to_hastebin(string)
                await message.edit(
                    content=f":x: Content too long. {link}",
                    embed=None)
                return
        if len(result) >= 2:
            if (len(result[1]) >= 1024):
                stdout = result[0].decode('utf-8')
                string = string + f'[[STDERR]]\n{stdout}'
                link = await self.post_to_hastebin(string)
                await message.edit(
                    content=f":x: Content too long. {link}",
                    embed=None)
                return
        embed.add_field(
            name="stdout",
            value=f'```{stdout}```' if 'stdout' in locals() else 'No output.',
            inline=False)
        embed.add_field(
            name="stderr",
            value=f'```{stderr}```' if 'stderr' in locals() else 'No output.',
            inline=False)
        await message.edit(content='', embed=embed)

    @commands.command(aliases=['game', 'status'])
    @permissions.owner()
    async def setgame(self, ctx, *, status: str):
        await ctx.bot.change_presence(game=discord.Game(name=status, type=0))
        await ctx.send(':ok_hand:')

    @commands.command()
    @permissions.owner()
    async def maintenance(self, ctx, state: str=None):
        bools = False
        if state is not None:
            if state in ['true', 'false', 'on', 'off']:
                bools = state in ['on', 'true']

        if bools == True:
            prompt = await ctx.send('```Are you sure you want to do this? This will make the bot stop responding to anyone but you!\n\n[y]: Enter Maintenance mode\n[n]: Exit prompt```')
            poll = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel)
            if poll.content == 'y':
                await prompt.delete()
                await self.bot.change_presence(status=discord.Status.dnd, game=None)
                self.bot.maintenance = True
                await ctx.send(':white_check_mark: Bot in maintenance mode.')
                return
            else:
                await prompt.delete()
                await ctx.send('Prompt exited.')
        elif bools == False:
            self.bot.maintenance = False
            await self.bot.change_presence(game=discord.Game(
                name=f'{self.bot.prefix[0]}help',
                type=2))
            await ctx.send(':white_check_mark: Bot in regular mode.')

    @commands.command()
    @permissions.owner()
    async def git(self, ctx, sub, flags=""):
        """Runs some git commands in Discord."""

        if sub == "gud":
            if not flags:
                return await ctx.send("```You are now so gud!```")
            else:
                return await ctx.send(
                    "```{} is now so gud!```".format(flags))
        elif sub == "rekt":
            if not flags:
                return await ctx.send("```You got #rekt!```")
            else:
                return await ctx.send(
                    "```{} got #rekt!```".format(flags))
        else:
            process_msg = await ctx.send(
                "<a:typing:401162479041773568> Processing...")
            process = subprocess.Popen(
                f"git {sub + flags}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            res = process.communicate()
            if res[0] == b'':
                content = "Successful!"
            else:
                content = res[0].decode("utf8")
            return await process_msg.edit(content=f"```{content}```")

    def parse_google_card(self, node):
        e = discord.Embed(colour=discord.Colour.blurple())

        # check if it's a calculator card:
        calculator = node.find(".//span[@class='cwclet']")
        if calculator is not None:
            e.title = 'Calculator'
            result = node.find(".//span[@class='cwcot']")
            if result is not None:
                result = ' '.join((calculator.text, result.text.strip()))
            else:
                result = calculator.text + ' ???'
            e.description = result
            return e

        # check for unit conversion card

        unit_conversions = node.xpath(
            ".//input[contains(@class, '_eif') and @value]")
        if len(unit_conversions) == 2:
            e.title = 'Unit Conversion'

            # the <input> contains our values, first value = second value essentially.
            # these <input> also have siblings with <select> and <option selected=1>
            # that denote what units we're using

            # We will get 2 <option selected="1"> nodes by traversing the parent
            # The first unit being converted (e.g. Miles)
            # The second unit being converted (e.g. Feet)

            xpath = etree.XPath(
                "parent::div/select/option[@selected='1']/text()")
            try:
                first_node = unit_conversions[0]
                first_unit = xpath(first_node)[0]
                first_value = float(first_node.get('value'))
                second_node = unit_conversions[1]
                second_unit = xpath(second_node)[0]
                second_value = float(second_node.get('value'))
                e.description = ' '.join(
                    (str(first_value), first_unit, '=', str(second_value), second_unit))
            except Exception:
                return None
            else:
                return e

        # check for currency conversion card
        if 'currency' in node.get('class', ''):
            currency_selectors = node.xpath(
                ".//div[@class='ccw_unit_selector_cnt']")
            if len(currency_selectors) == 2:
                e.title = 'Currency Conversion'
                # Inside this <div> is a <select> with <option selected="1"> nodes
                # just like the unit conversion card.

                first_node = currency_selectors[0]
                first_currency = first_node.find(
                    "./select/option[@selected='1']")

                second_node = currency_selectors[1]
                second_currency = second_node.find(
                    "./select/option[@selected='1']")

                # The parent of the nodes have a <input class='vk_gy vk_sh
                # ccw_data' value=...>
                xpath = etree.XPath(
                    "parent::td/parent::tr/td/input[@class='vk_gy vk_sh ccw_data']")
                try:
                    first_value = float(xpath(first_node)[0].get('value'))
                    second_value = float(xpath(second_node)[0].get('value'))

                    values = (
                        str(first_value),
                        first_currency.text,
                        f'({first_currency.get("value")})',
                        '=',
                        str(second_value),
                        second_currency.text,
                        f'({second_currency.get("value")})'
                    )
                    e.description = ' '.join(values)
                except Exception:
                    return None
                else:
                    return e

        # check for generic information card
        info = node.find(".//div[@class='_f2g']")
        if info is not None:
            try:
                e.title = ''.join(info.itertext()).strip()
                actual_information = info.xpath(
                    "parent::div/parent::div//div[@class='_XWk' or contains(@class, 'kpd-ans')]")[0]
                e.description = ''.join(actual_information.itertext()).strip()
            except Exception:
                return None
            else:
                return e

        # check for translation card
        translation = node.find(".//div[@id='tw-ob']")
        if translation is not None:
            src_text = translation.find(".//pre[@id='tw-source-text']/span")
            src_lang = translation.find(
                ".//select[@id='tw-sl']/option[@selected='1']")

            dest_text = translation.find(".//pre[@id='tw-target-text']/span")
            dest_lang = translation.find(
                ".//select[@id='tw-tl']/option[@selected='1']")

            # TODO: bilingual dictionary nonsense?

            e.title = 'Translation'
            try:
                e.add_field(name=src_lang.text,
                            value=src_text.text, inline=True)
                e.add_field(name=dest_lang.text,
                            value=dest_text.text, inline=True)
            except Exception:
                return None
            else:
                return e

        # check for "time in" card
        time = node.find("./div[@class='vk_bk vk_ans']")
        if time is not None:
            date = node.find("./div[@class='vk_gy vk_sh']")
            try:
                e.title = node.find('span').text
                e.description = f'{time.text}\n{"".join(date.itertext()).strip()}'
            except Exception:
                return None
            else:
                return e

        # time in has an alternative form without spans
        time = node.find("./div/div[@class='vk_bk vk_ans _nEd']")
        if time is not None:
            converted = "".join(time.itertext()).strip()
            try:
                # remove the in-between text
                parent = time.getparent()
                parent.remove(time)
                original = "".join(parent.itertext()).strip()
                e.title = 'Time Conversion'
                e.description = f'{original}...\n{converted}'
            except Exception:
                return None
            else:
                return e

        # check for definition card
        words = node.xpath(".//span[@data-dobid='hdw']")
        if words:
            lex = etree.XPath(".//div[@class='lr_dct_sf_h']/i/span")

            # this one is derived if we were based on the position from lex
            xpath = etree.XPath("../../../ol[@class='lr_dct_sf_sens']//"
                                "div[not(@class and @class='lr_dct_sf_subsen')]/"
                                "div[@class='_Jig']/div[@data-dobid='dfn']/span")
            for word in words:
                # we must go two parents up to get the root node
                root = word.getparent().getparent()

                pronunciation = root.find(".//span[@class='lr_dct_ph']/span")
                if pronunciation is None:
                    continue

                lexical_category = lex(root)
                definitions = xpath(root)

                for category in lexical_category:
                    definitions = xpath(category)
                    try:
                        descrip = [f'*{category.text}*']
                        for index, value in enumerate(definitions, 1):
                            descrip.append(f'{index}. {value.text}')

                        e.add_field(
                            name=f'{word.text} /{pronunciation.text}/', value='\n'.join(descrip))
                    except:
                        continue

            return e

        # check for weather card
        location = node.find("./div[@id='wob_loc']")
        if location is None:
            return None

        # these units should be metric

        date = node.find("./div[@id='wob_dts']")

        # <img alt="category here" src="cool image">
        category = node.find(".//img[@id='wob_tci']")

        xpath = etree.XPath(
            ".//div[@id='wob_d']//div[contains(@class, 'vk_bk')]//span[@class='wob_t']")
        temperatures = xpath(node)

        misc_info_node = node.find(".//div[@class='vk_gy vk_sh wob-dtl']")

        if misc_info_node is None:
            return None

        precipitation = misc_info_node.find("./div/span[@id='wob_pp']")
        humidity = misc_info_node.find("./div/span[@id='wob_hm']")
        wind = misc_info_node.find("./div/span/span[@id='wob_tws']")

        try:
            e.title = 'Weather for ' + location.text.strip()
            e.description = f'*{category.get("alt")}*'
            e.set_thumbnail(url='https:' + category.get('src'))

            if len(temperatures) == 4:
                first_unit = temperatures[0].text + temperatures[2].text
                second_unit = temperatures[1].text + temperatures[3].text
                units = f'{first_unit} | {second_unit}'
            else:
                units = 'Unknown'

            e.add_field(name='Temperature', value=units, inline=False)

            if precipitation is not None:
                e.add_field(name='Precipitation', value=precipitation.text)

            if humidity is not None:
                e.add_field(name='Humidity', value=humidity.text)

            if wind is not None:
                e.add_field(name='Wind', value=wind.text)
        except:
            return None

        return e

    async def get_google_entries(self, query):
        url = f'https://www.google.com/search?q={uriquote(query)}'
        params = {
            'safe': 'on',
            'lr': 'lang_en',
            'hl': 'en'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) Gecko/20100101 Firefox/53.0'
        }

        # list of URLs and title tuples
        entries = []

        # the result of a google card, an embed
        card = None

        async with self.aioclient.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                raise RuntimeError('Google has failed to respond.')

            root = etree.fromstring(await resp.text(), etree.HTMLParser())

            # for bad in root.xpath('//style'):
            #     bad.getparent().remove(bad)

            # for bad in root.xpath('//script'):
            #     bad.getparent().remove(bad)

            # with open('google.html', 'w', encoding='utf-8') as f:
            #     f.write(etree.tostring(root, pretty_print=True).decode('utf-8'))

            """
            Tree looks like this.. sort of..
            <div class="rc">
                <h3 class="r">
                    <a href="url here">title here</a>
                </h3>
            </div>
            """

            card_node = root.xpath(".//div[@id='rso']/div[@class='_NId']//"
                                   "div[contains(@class, 'vk_c') or @class='g mnr-c g-blk' or @class='kp-blk']")

            if card_node is None or len(card_node) == 0:
                card = None
            else:
                card = self.parse_google_card(card_node[0])

            search_results = root.findall(".//div[@class='rc']")
            # print(len(search_results))
            for node in search_results:
                link = node.find("./h3[@class='r']/a")
                if link is not None:
                    # print(etree.tostring(link, pretty_print=True).decode())
                    entries.append((link.get('href'), link.text))

        return card, entries

    @commands.command(aliases=['g', 'search'])
    async def google(self, ctx, query: str):
        """Searches google and gives you top result."""
        await ctx.trigger_typing()
        try:
            card, entries = await self.get_google_entries(query)
        except RuntimeError as e:
            await ctx.send(str(e))
        else:
            if card:
                value = '\n'.join(
                    f'[{title}]({url.replace(")", "%29")})'
                    for url, title in entries[:3])
                if value:
                    card.add_field(name='Search Results',
                                   value=value, inline=False)
                return await ctx.send(embed=card)

            if len(entries) == 0:
                return await ctx.send('No results found... sorry.')

            next_two = [x[0] for x in entries[1:3]]
            first_entry = entries[0][0]
            if first_entry[-1] == ')':
                first_entry = first_entry[:-1] + '%29'

            if next_two:
                formatted = '\n'.join(f'<{x}>' for x in next_two)
                answer = f'{first_entry}\n\n**See also:**\n{formatted}'
            else:
                answer = first_entry

            await ctx.send(answer)

    @commands.command(aliases=['contest', 'vote'])
    async def poll(self, ctx, question: str, time: int=120,
                   *emojis: Union[discord.Emoji, str]):
        """Creates a poll with reaction options."""
        emojis = set(emojis)  # Remove duplicates
        if len(emojis) <= 1:
            return await ctx.send(
                "\u274C Cannot start poll with one option or less.",
                delete_after=3)

        # Initial poll message
        poll = (
            f"**{ctx.author.mention}** asks: {question}\n\n"
            f"_Poll active for {time} seconds. React below to vote._")
        async with ctx.channel.typing():
            poll_msg = await ctx.send(poll)
            for emoji in emojis:
                try:
                    await poll_msg.add_reaction(emoji)
                except discord.NotFound:
                    pass

        asyncio.sleep(time)  # Users are reacting

        # End of poll
        results_emojis = [reaction.emoji for reaction in poll_msg.reactions
                          if reaction.emoji in emojis]
        results_count = collections.Counter(results_emojis)
        results = f"**Poll by {ctx.author} ended!**\n\n"
        for emoji, count in results_count.most_common():
            results += f"{emoji}: _{count}_ \n"
        await ctx.send(results)


def setup(bot):
    bot.add_cog(Utility(bot))
