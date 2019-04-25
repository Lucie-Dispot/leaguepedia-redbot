from redbot.core import commands
import discord
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

    @commands.command()
    async def player(self, ctx):
        match = re.match('^!player (.*)', ctx.message.content)
        result = site.api('cargoquery', tables='InfoboxPlayer', fields='ID,Image,Name,Team,Role', where='ID="{0}"'.format(match.group(1)))
        if not result['cargoquery']:
            await ctx.send('Unknown player')
        else:
            # Pretty print
            player_infos = result['cargoquery'][0]['title']
            print(player_infos)
            embed = discord.Embed(title=player_infos['ID'], description=player_infos['Name'], url='https://lol.gamepedia.com/{0}'.format(player_infos['ID'].replace(' ', '_')))
            embed.set_thumbnail(url='https://lol.gamepedia.com/Special:Filepath/{0}'.format(player_infos['Image'].replace(' ', '_')))
            team = player_infos['Team']
            if not team:
                team = 'No current team'
            embed.add_field(name='Team', value=team, inline=True)
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Leaguepedia())
