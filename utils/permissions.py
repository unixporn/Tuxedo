from discord.ext import commands


async def is_owner_check(ctx):
    if str(ctx.author.id) in ctx.bot.config.get('OWNERS'):
        return True
    await ctx.send(":x: Must be a bot owner.",
                   delete_after=3)
    return False


async def is_moderator_check(ctx):
    for role in ctx.author.roles:
        if str(role.id) in ctx.bot.config.get('MOD_ROLES'):
            return True
    await ctx.send(":x: Must be a moderator.",
                   delete_after=3)
    return False


async def is_helper_check(ctx):
    for role in ctx.author.roles:
        if (str(role.id) in ctx.bot.config.get('MOD_ROLES')) or (
                str(role.id) in ctx.bot.config.get('HELPER_ROLES')):
            return True
    await ctx.send(":x: Must be a helper or moderator.",
                   delete_after=3)
    return False


def owner_id_check(bot, _id):
    return str(_id) in bot.config.get('OWNERS')


def owner():
    return commands.check(is_owner_check)


def moderator():
    return commands.check(is_moderator_check)


def helper():
    return commands.check(is_helper_check)
