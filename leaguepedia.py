from redbot.core import commands
from datetime import datetime
import urllib.parse
import discord
import mwclient
import re

site = mwclient.Site('lol.gamepedia.com', path='/')

INT_TO_EMOJI = [':zero:', ':one:', ':two:', ':three:', ':four:', ':five:', ':six:', ':seven:', ':eight:', ':nine:']
EMOJI_TO_INT = ['0⃣', '1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣']

def sortByDate(object):
    return object['title']['DateTime UTC']

def formatPlayerInfos(player_infos):
    print(player_infos)
    embed = discord.Embed(title=player_infos['ID'], description=player_infos['Name'], url='https://lol.gamepedia.com/{0}'.format(urrlib.parse.quote(player_infos['ID'].replace(' ', '_'))))
    embed.set_thumbnail(url='https://lol.gamepedia.com/Special:Filepath/{0}'.format(urllib.parse.quote(player_infos['Image'].replace(' ', '_'))))
    team = player_infos['Team']
    if not team:
        team = 'No current team'
    embed.add_field(name='Role', value=player_infos['Role'], inline=True)
    embed.add_field(name='Team', value=team, inline=True)
    return embed

class Leaguepedia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Reacts to reactions to the player disambig prompts & sends info on a right reaction
    async def player_reaction_listener(self, reaction, user):
        # Don't answer if the original message isn't from the bot
        if reaction.message.author != self.bot.user:
            return
        # Don't answer if this reaction already has been sent
        if reaction.count > 1:
            return
        message = reaction.message.content.split('\n')
        if (message[0] == 'Multiple players found for this query:'):
            # Get the disambig line from the reaction
            line_id = EMOJI_TO_INT.index(str(reaction))
            line = message[line_id]
            # Ignore if wrong line
            if line.startswith(INT_TO_EMOJI[line_id]):
                player_full_name = line[len(INT_TO_EMOJI[line_id])+1:].split(' |')[0][:-1].split('(')
                print(player_full_name)
                result = site.api('cargoquery', tables='InfoboxPlayer', fields='ID,Image,Name,Team,Role', where='Name="{0}" and ID="{1}"'.format(player_full_name[1], player_full_name[0]))
                print(result)
                player_infos = result['cargoquery'][0]['title']
                embed = formatPlayerInfos(player_infos)
                await ctx.send(embed=embed)

    # Returns information regarding the requested player.
    @commands.command()
    async def player(self, ctx):
        """
        Usage: [prefix]player <player>
        Prints useful information and stats about the given player.
        In case of an ambiguity in the player name, you will be prompted with the ambiguous players.
        """
        regex_string = r'^' + re.escape(ctx.prefix) + r'player (.*)'
        match = re.match(regex_string, ctx.message.content)
        if not match:
            await ctx.send('`Usage: {0}player <player>`'.format(ctx.prefix))
            return
        player_name = match.group(1)
        # First query the disambig page
        disambig_result = site.api('cargoquery', tables='PlayerDisambig', fields='Name,Region,Team,Role', limit='5', where='Name LIKE "%{0}%"'.format(player_name))
        # If there is more than one disambig result, prompt the user for the actual player
        if disambig_result['cargoquery']:
            # Prompt the user & override player_name with selected user
            disambig_prompt = 'Multiple players found for this query:\n'
            i = 0
            for player_ambig in disambig_result['cargoquery']:
                i += 1
                disambig_prompt += '{0} {1} | Team: {2} - Role: {3} - Region: {4}\n'.format(INT_TO_EMOJI[i], player_ambig['title']['Name'], player_ambig['title']['Team'], player_ambig['title']['Role'], player_ambig['title']['Region'])
            disambig_prompt += 'Please react to this query specifying the number of the player you are looking for.'
            await ctx.send(disambig_prompt)
        else:
            result = site.api('cargoquery', tables='InfoboxPlayer', fields='ID,Image,Name,Team,Role', where='Name LIKE "%{0}%" OR ID LIKE "{0}"'.format(player_name))
            if not result['cargoquery']:
                await ctx.send('`Unknown player`')
                return
            # Pretty print
            player_infos = result['cargoquery'][0]['title']
            embed = formatPlayerInfos(player_infos)
            await ctx.send(embed=embed)

    @commands.command()
    async def upcoming(self, ctx):
        """
        Usage: [prefix]upcoming <league>
        Prints the upcoming schedule of the 5 next matches for the specified league.
        Note: matches on league only (ex: msi, lec, lcs). League name is case insensitive.
        If no league is specified, prints the upcoming schedule for all leagues.
        """
        # Two cases: global upcoming or with argument
        display_tournaments = []
        regex_string = r'^' + re.escape(ctx.prefix) + r'upcoming (.*)'
        regex = re.match(regex_string, ctx.message.content)
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
            await ctx.send('`This tournament isn\'t currently active`')
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
    cog = Leaguepedia(bot)
    bot.add_cog(cog)
    bot.add_listener(cog.player_reaction_listener, 'on_reaction_add')
