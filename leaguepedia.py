from redbot.core import commands
from datetime import datetime
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
            embed = discord.Embed(title=player_infos['ID'], description=player_infos['Name'], url='https://lol.gamepedia.com/{0}'.format(player_infos['ID'].replace(' ', '_')))
            embed.set_thumbnail(url='https://lol.gamepedia.com/Special:Filepath/{0}'.format(player_infos['Image'].replace(' ', '_')))
            team = player_infos['Team']
            if not team:
                team = 'No current team'
            embed.add_field(name='Role', value=player_infos['Role'], inline=True)
            embed.add_field(name='Team', value=team, inline=True)
            await ctx.send(embed=embed)

    @commands.command()
    async def upcoming(self, ctx):
        results = site.api('cargoquery', tables='MatchSchedule', fields='Team1,Team2,DateTime_UTC,ShownName,Round,Stream,OverviewPage', limit=5, order_by='DateTime_UTC ASC', where='DateTime_UTC > NOW() - INTERVAL 3 HOUR AND WINNER IS NULL')
        embed = discord.Embed(title='Upcoming matches')
        tournaments = ''
        matchups = ''
        for match in results['cargoquery']:
            date = datetime.strptime(match['title']['DateTime UTC'], '%Y-%m-%d %H:%M:%S')
            delta = date - datetime.utcnow()
            formatted_time = '{0}h {1}m'.format(delta.seconds // 3600, (delta.seconds // 60) % 60)
            tournaments += '[{0}]({1})'.format(formatted_time, match['title']['Stream'])
            matchups += '| [{0}](https://lol.gamepedia.com/{1}) vs [{2}](https://lol.gamepedia.com/{3})\n'.format(match['title']['Team1'], match['title']['Team1'].replace(' ', '_'), match['title']['Team2'], match['title']['Team2'].replace(' ', '_'))
            tournaments += ' | [{0}](https://lol.gamepedia.com/{1})\n'.format(match['title']['ShownName'], match['title']['OverviewPage'].replace(' ', '_'))
        embed.add_field(name='Timer     Tournament', inline=True, value=tournaments)
        embed.add_field(name='Match', inline=True, value=matchups)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Leaguepedia())
