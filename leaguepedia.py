from redbot.core import commands
from datetime import datetime
import discord
import mwclient
import re

site = mwclient.Site('lol.gamepedia.com', path='/')

def sortByDate(object):
    return object['title']['DateTime UTC']

class Leaguepedia(commands.Cog):
    # Test command.
    # Returns the name and base health of the five first champions in the game.
    @commands.command()
    async def champions(self, ctx):
        result = site.api('cargoquery', tables='InfoboxChampion', fields='Name,Health', limit=5)
        # Note: Discord doesn't support tables
        msg = '| Name | Health |\n| ------ | ------ |\n'
        for champion in result['cargoquery']:
            msg += '| {0} | {1} |\n'.format(champion['title']['Name'], champion['title']['Health'])
        await ctx.send(msg)

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
        # Two cases: global upcoming or with argument
        display_tournaments = []
        regex = re.match('^!upcoming (.*)', ctx.message.content)
        if regex:
            # Get League from CCMTournaments
            tournaments_results = site.api('cargoquery', tables='CCMTournaments', fields='OverviewPage,StandardName', order_by='Year DESC', where='lower(League)="{0}"'.format(regex.group(1).lower()))
            # TODO Find closest match if no results
            if not tournaments_results['cargoquery']:
                await ctx.send('Tournament not found')
                return
            else:
                current_leagues = site.api('cargoquery', tables='CCCurrentLeagues', fields='Event')['cargoquery']
                for tournament in tournaments_results['cargoquery']:
                    # If the tournament is found in current_leagues, fetch its information and add it to the display_tournaments list
                    found = False
                    for league in current_leagues:
                        if league['title']['Event'] == tournament['title']['StandardName']:
                            found = True
                    if found:
                        tournament_details = site.api('cargoquery', tables='MatchSchedule', fields='Team1,Team2,DateTime_UTC,ShownName,Round,Stream,OverviewPage', limit=5, order_by='DateTime_UTC ASC', where='DateTime_UTC > NOW() AND WINNER IS NULL AND OverviewPage="{0}"'.format(tournament['title']['OverviewPage']))
                        display_tournaments = display_tournaments + tournament_details['cargoquery']
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
            embed = discord.Embed(title='Upcoming matches', url='https://lol.gamepedia.com/Special:RunQuery/SpoilerFreeSchedule?SFS[1]={0}&pfRunQueryFormName=SpoilerFreeSchedule'.format(display_tournaments[0]['title']['OverviewPage']).replace(' ', '%20'))
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
            matchups += '[{0}](https://lol.gamepedia.com/{1}) vs [{2}](https://lol.gamepedia.com/{3})\n'.format(team1_tag, match['title']['Team1'].replace(' ', '_'), team2_tag, match['title']['Team2'].replace(' ', '_'))

            tournaments += '[{0}](https://lol.gamepedia.com/{1})\n'.format(match['title']['ShownName'], match['title']['OverviewPage'].replace(' ', '_'))
        embed.add_field(name='Tournament', inline=True, value=tournaments)
        embed.add_field(name='Match', inline=True, value=matchups)
        embed.add_field(name='Countdown', inline=True, value=times)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Leaguepedia())
