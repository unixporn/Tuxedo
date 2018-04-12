from discord.ext import commands
import aiohttp
import random


class Search:
    def __init__(self, bot):
        self.conn = bot.conn
        self.bot = bot
        self.session = aiohttp.ClientSession()

    @commands.command()
    async def search(self, ctx, *, query: str):
        with open('searxes.txt') as instances:
            instance = random.sample(instances.read().split('\n'), k=1)
        call = f'https://{instance[0]}/search?q={query}&format=json'
        async with session.get('call') as resp:
            response = await resp.json()

        # infoboxes = response['infoboxes']
        results = response['results']

        msg = f"Showing **5** results for `{query}`. \n\n"
        msg += (f"**{results[0]['title']}** <{results[0]['url']}>\n"
                f"{results[0]['content']}\n\n")
        msg += "\n".join(
            [f'**{entry.title}** <{entry.url}>' for entry in results[1:4]])
        msg += f"\n_Results retrieved from instance `{instance}`._"

        await ctx.send(msg)


def setup(bot):
    bot.add_cog(Search(bot))
