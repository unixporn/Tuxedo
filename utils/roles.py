"""Roles Util"""

import discord
from discord.ext import commands
import discord.utils as dutils
from typing import List


class UnknownRole(commands.CommandError):
    """Thrown when role cannot be found."""
    pass


def get_group(ctx, group: str) -> List[discord.Role]:
    """Retrieves a group of roles via separator role."""
    group_name = f"------- {group} -------"
    separator = dutils.get(ctx.guild.roles, name=group_name)
    if not separator:
        raise UnknownRole(group_name)
    group_roles = []

    for role in ctx.guild.role_hierarchy:
        if role.position < separator.position:
            if role.name.startswith('-------') or role.name == 'everyone':
                break  # End of group found
            group_roles.append(role)

    return group_roles
