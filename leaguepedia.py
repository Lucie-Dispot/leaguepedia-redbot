from redbot.core import commands
from datetime import datetime
import urllib.parse
import discord
import mwclient
import re

site = mwclient.Site('lol.gamepedia.com', path='/')

def sortByDate(object):
    return object['title']['DateTime UTC']

class Leaguepedia(commands.Cog):
    # Returns information regarding the requested player.
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
        """
        Usage: !upcoming <league>
        Prints the upcoming schedule of the 5 next matches for the specified league.
        Note: matches on league only (ex: msi, lec, lcs). League name is case insensitive.
        If no league is specified, prints the upcoming schedule for all leagues.
        """
        # Two cases: global upcoming or with argument
        display_tournaments = []
        regex = re.match('^!upcoming (.*)', ctx.message.content)
        if regex:
            # Get League from CCMTournaments
            tournaments_results = site.api('cargoquery', tables='CCMTournaments', fields='OverviewPage,StandardName', order_by='Year DESC', where='League LIKE "{0}"'.format(regex.group(1)))
            # If it matches one or more tournaments, use the matches from those tournaments
            if tournaments_results['cargoquery']:
                for tournament in tournaments_results['cargoquery']:
                    # Fetch the tournament's information and add it to the display_tournaments list
                    tournament_details = site.api('cargoquery', tables='MatchSchedule', fields='Team1,Team2,DateTime_UTC,ShownName,Round,Stream,OverviewPage', limit=5, order_by='DateTime_UTC ASC', where='DateTime_UTC > NOW() AND WINNER IS NULL AND OverviewPage="{0}"'.format(tournament['title']['OverviewPage']))
                    display_tournaments = display_tournaments + tournament_details['cargoquery']
            else:
                # If it doesn't match a tournament, try to get results directly from MatchSchedule
                display_tournaments = site.api('cargoquery', tables='MatchSchedule', fields='Team1,Team2,DateTime_UTC,ShownName,Round,Stream,OverviewPage', limit=5, order_by='DateTime_UTC ASC', where='DateTime_UTC > NOW() AND WINNER IS NULL AND (ShownName LIKE "%{0}%" OR OverviewPage LIKE "%{0}%")'.format(regex.group(1)))['cargoquery']
        else:
            # Global upcoming games
            results = site.api('cargoquery', tables='MatchSchedule', fields='Team1,Team2,DateTime_UTC,ShownName,Round,Stream,OverviewPage', limit=5, order_by='DateTime_UTC ASC', where='DateTime_UTC > NOW() AND WINNER IS NULL')
            display_tournaments = results['cargoquery']

        if len(display_tournaments) == 0:
            await ctx.send('This tournament isn\'t currently active')
            return
        # Sort final display_tournaments & reduce length to 5
        display_tournaments.sort(key=sortByDate)
        del display_tournaments[5:]

        if regex:
            embed = discord.Embed(title='Upcoming matches', url='https://lol.gamepedia.com/Special:RunQuery/SpoilerFreeSchedule?SFS[1]={0}&pfRunQueryFormName=SpoilerFreeSchedule'.format(urllib.parse.quote(display_tournaments[0]['title']['OverviewPage'])))
        else:
            embed = discord.Embed(title='Upcoming matches')
        times = ''
        tournaments = ''
        matchups = ''
        for match in display_tournaments:
            date = datetime.strptime(match['title']['DateTime UTC'], '%Y-%m-%d %H:%M:%S')
            delta = date - datetime.utcnow()
            formatted_time = '{0}h {1}m'.format(delta.seconds // 3600, (delta.seconds // 60) % 60)
            if delta.days > 0:
                formatted_time = '{0}d '.format(delta.days) + formatted_time
            times += '[{0}]({1})\n'.format(formatted_time, match['title']['Stream'])

            # Request page for each team & get short name
            team1_tag = site.expandtemplates('{{Team|' + match['title']['Team1'].lower() + '|short}}')
            team2_tag = site.expandtemplates('{{Team|' + match['title']['Team2'].lower() + '|short}}')
            matchups += '[{0}](https://lol.gamepedia.com/{1}) vs [{2}](https://lol.gamepedia.com/{3})\n'.format(team1_tag, urllib.parse.quote(match['title']['Team1'].replace(' ', '_')), team2_tag, urllib.parse.quote(match['title']['Team2'].replace(' ', '_')))

            tournaments += '[{0}](https://lol.gamepedia.com/{1})\n'.format(match['title']['ShownName'], urllib.parse.quote(match['title']['OverviewPage'].replace(' ', '_')))
        embed.add_field(name='Tournament', inline=True, value=tournaments)
        embed.add_field(name='Match', inline=True, value=matchups)
        embed.add_field(name='Countdown', inline=True, value=times)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Leaguepedia())
