from discord.ext import commands


def is_owner_check(ctx):
    return str(ctx.message.author.id) in ctx.bot.config.get('OWNERS')


def is_moderator_check(ctx):
    for role in ctx.message.author.roles:
        if str(role.id) is ctx.bot.config.get('MOD_ROLES'):
            return True
    return False


def is_helper_check(ctx):
    for role in ctx.message.author.roles:
        if (str(role.id) in ctx.bot.config.get('MOD_ROLES')) or (
                str(role.id) in ctx.bot.config.get('HELPER_ROLES')):
            return True
    return False


def owner_id_check(bot, _id):
    return str(_id) in bot.config.get('OWNERS')


def owner():
    return commands.check(is_owner_check)


def moderator():
    return commands.check(is_moderator_check)


def helper():
    return commands.check(is_helper_check)
