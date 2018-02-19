"""Profile Extension"""

import discord
import asyncio
from discord.ext import commands
from discord import utils as dutils
from utils import permissions, roles


class Profile:
    """Commands to set up roles and colors."""

    def __init__(self, bot):
        self.bot = bot

    def helper_str_check(self, r, u):  # HACK Unclean, should be in util
        for role in u.roles:
            if (str(role.id) in self.bot.config.get(
                    'MOD_ROLES')) or (
                str(role.id) in self.bot.config.get(
                    'HELPER_ROLES')):
                return True
        return False

    @commands.group(name='setup',
                    aliases=['desktop', 'rice'])
    async def desktop_setup(self, ctx, *requested: str):
        """Adds setup tags to a user, dynamically."""
        if len(requested) == 0:
            raise commands.errors.MissingRequiredArgument(ctx)
        group = roles.get_group(ctx, 'setups')

        # Role Holders
        to_add = []
        to_request = []
        to_deny = []

        # Block indicators
        group_top = group[0]
        group_bottom = group[-1]
        del group[0], group[-1]

        # Stringify and lowercase
        requested = (arg.lower() for arg in requested)

        for request in requested:
            # Matches to role, assigns first result if exists
            existing = [role for role in group
                        if role.name.lower() == request]
            try:
                role = existing[0]
            except IndexError:
                to_request.append(request)
                continue
            # Within group?
            if (role.position >= group_top.position or
                    role.position <= group_bottom.position):
                to_deny.append(role)
            else:
                to_add.append(role)

        if to_deny:
            await ctx.send(
                "\u274C Some roles could not be added:\n\n"
                f"`{', '.join([role.name for role in to_deny])}`\n\n"
                f"They conflict with preexisting management roles.",
                delete_after=30)
            if to_add == [] or to_deny == []:
                return
        await ctx.author.add_roles(*to_add)
        if to_request:
            try:
                if self.helper_str_check(None, ctx.author):
                    override = True
                else:
                    # Member Notice
                    confirm_msg = await ctx.send(
                        "\u274C Some roles were not found:\n\n"
                        f"`{', '.join(to_request)}`\n\n"
                        f"A staff member will verify shortly.")

                    # Staff Notification
                    staff_channel = dutils.get(
                        ctx.guild.channels,
                        id=int(self.bot.config["STAFF_CHANNEL"]))
                    request_msg = await staff_channel.send(
                        f"\u274C @here Please verify roles for `{ctx.author}`:"
                        f"\n\n`{', '.join(to_request)}`\n\n")
                    await request_msg.add_reaction("\u2705")
                    await request_msg.add_reaction("\u274C")

                    # Looks at staff notification
                    event = await self.bot.wait_for(
                        'reaction_add',
                        timeout=300.0,
                        check=self.helper_str_check)

            except asyncio.TimeoutError:
                await ctx.send(  # FIXME Always times out
                    f"\u274C {ctx.author.mention} Your request timed out. "
                    "Please contact a staff member directly at a later date.",
                    delete_after=30)

            else:
                # XXX This section is weird
                try:
                    accept = (event[0].emoji == "\u2705")
                except NameError:
                    accept = override

                if accept:
                    accepted_add = []
                    for name in to_request:
                        role = await ctx.guild.create_role(
                            name=name)
                        role.edit(position=group[0].position - 1)
                        accepted_add.append(role)
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

    # @setup.command(aliases=["delete", "rm", "del"])
    # async def _setup_remove(self, ctx, *requested: str):
    #     to_remove = []
    #     async with self.bot.typing():
    #         for request in requested:
    #             role = dutils.get(ctx.author.roles, name=request)
    #             if role:
    #                 to_remove.append(role)
    #         await ctx.author.remove_roles(
    #             *to_remove, reason='setup remove')
    #         await ctx.send(f"Roles removed:\n\n{', '.join(to_remove)}")

    @commands.command(name="color")
    async def give_color(self, ctx, color: discord.Color):
        """Gives user a custom color role."""
        if str(color) in ["#ff4646", "#f1c40f", "#2ecc71"]:
            return await ctx.send(f"\u274C `{str(color)}` is reserved.")
        group = roles.get_group(ctx, 'colors')
        role = [existing for existing in group
                if existing.name == str(color)]
        async with ctx.channel.typing():
            try:
                await ctx.author.add_roles(role[0])
            except IndexError:
                role = await ctx.guild.create_role(
                    name=str(color),
                    color=color,
                    reason='color add')
                await role.edit(
                    position=group[0].position - 1)
                await ctx.author.add_roles(role, reason='color add')
                await ctx.send(f"\u2705 Color `{str(color)}` added!")


def setup(bot):
    bot.add_cog(Profile(bot))
