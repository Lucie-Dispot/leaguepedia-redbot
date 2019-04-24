from redbot.core import commands
import mwclient
import re

site = mwclient.Site('lol.gamepedia.com', path='/')

class Leaguepedia(commands.Cog):
    @commands.command()
    async def champions(self, ctx):
        result = site.api('cargoquery', tables='InfoboxChampion', fields='Name,Health', limit=5)
        # Note: Discord doesn't support tables
        msg = '| Name | Health |\n| ------ | ------ |\n'
        for champion in result['cargoquery']:
            msg += '| {0} | {1} |\n'.format(champion['title']['Name'], champion['title']['Health'])
        await ctx.send(msg)

def setup(bot):
    bot.add_cog(Leaguepedia())
