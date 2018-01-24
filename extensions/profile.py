import asyncio
from discord.ext import commands
from discord import utils as dutils
from utils import permissions


class Profile:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='setup',
                      aliases=['desktop', 'rice'])
    async def desktop_setup(self, ctx, *args):
        '''Adds setup tags to a user, dynamically.'''

        to_add = []
        to_request = []
        to_deny = []
        block_top = dutils.get(ctx.guild.roles, name="------- setups -------")

        for item in args:
            roles = [existing for existing in ctx.guild.roles
                     if existing.name.lower() == item.lower()]
            try:
                role = roles[0]
            except:
                role = None
            if role is None:
                to_request.append(item)
            elif role.position < block_top.position:
                to_add.append(role)
            else:
                to_deny.append(role)

        if to_deny != []:
            await ctx.send(
                "\u274C Some roles could not be added:\n\n"
                f"`{', '.join([role.name for role in to_deny])}`\n\n"
                f"They conflict with preexisting management roles.",
                delete_after=30)
            if to_add == [] or to_deny == []:
                return
        await ctx.author.add_roles(*to_add)
        if to_request != []:
            try:
                if permissions.is_helper_check(ctx):
                    override = True
                else:
                    def react_check(r, u):
                        for role in u.roles:
                            if (str(role.id) in self.bot.config.get(
                                    'MOD_ROLES')) or (
                                str(role.id) in self.bot.config.get(
                                    'HELPER_ROLES')):
                                return True
                        return False
                    confirm_msg = await ctx.send(
                        "\u274C Some roles were not found:\n\n"
                        f"`{', '.join(to_request)}`\n\n"
                        f"A <@&400882287169896451> will be along to verify.")
                    staff_channel = dutils.get(
                        ctx.guild.channels, 
                        id=self.bot.config["STAFF_CHANNEL"])
                    request_msg = await staff_channel.send(
                        "\u274C @here Please verify roles:\n\n"
                        f"`{', '.join(to_request)}`\n\n")
                    await request_msg.add_reaction("\u2705")
                    await request_msg.add_reaction("\u274C")
                    event = await self.bot.wait_for(
                        'reaction_add',
                        timeout=300.0,
                        check=react_check)
            except asyncio.TimeoutError:
                await ctx.send(
                    f"\u274C {ctx.author.mention} Your request timed out. "
                    "Please contact a staff member directly at a later date.",
                    delete_after=30)
            else:
                try:
                    accept = (event[0].emoji == "\u2705")
                except NameError:
                    accept = override

                if accept:
                    accepted_add = []
                    for name in to_request:
                        accepted_add.append(await ctx.guild.create_role(
                            name=name))
                    await ctx.author.add_roles(*accepted_add)
                    try:
                        await confirm_msg.delete()
                    except NameError:
                        pass
                else:
                    await ctx.send(
                        f"\u274C {ctx.author.mention} Your request was "
                        "rejected. A staff member should explain to you soon.",
                        delete_after=30)
                    return

        await ctx.send(
            f"\u2705 {ctx.author.mention} Setup accepted!")


def setup(bot):
    bot.add_cog(Profile(bot))
