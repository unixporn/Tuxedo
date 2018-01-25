from discord.ext import commands


class WrongRole(commands.CommandError):
    """Says that you have the wrong role"""
    pass


async def is_owner_check(ctx):
    if str(ctx.author.id) in ctx.bot.config.get('OWNERS'):
        return True
    raise WrongRole(message="bot owner")
    return False


async def is_moderator_check(ctx):
    for role in ctx.author.roles:
        if str(role.id) in ctx.bot.config.get('MOD_ROLES'):
            return True
    raise WrongRole(message="moderator")
    return False


async def is_helper_check(ctx):
    for role in ctx.author.roles:
        if (str(role.id) in ctx.bot.config.get('MOD_ROLES')) or (
                str(role.id) in ctx.bot.config.get('HELPER_ROLES')):
            return True
    raise WrongRole(message="moderator or helper")
    return False


def owner_id_check(bot, _id):
    return str(_id) in bot.config.get('OWNERS')


def owner():
    return commands.check(is_owner_check)


def moderator():
    return commands.check(is_moderator_check)


def helper():
    return commands.check(is_helper_check)
