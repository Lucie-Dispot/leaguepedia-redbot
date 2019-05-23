# Leaguepedia red bot cog

## About

This is the red bot cog for Leaguepedia.  
Red bot is a modular Discord bot.  
Leaguepedia is the League of Legends esport wiki.  
This cog adds commands to red bot allowing to request Leaguepedia for data.

## Setup

### Prerequisites

* Python 3.7.0 or greater
* pip 9.0 or greater
* git

### Commands

```
pip install -U git+https://github.com/Cog-Creators/Red-DiscordBot@V3/develop#egg=redbot[test]

redbot-setup

redbot {name} # name is the name chosen during setup
```

During the last step you should be prompted for a token. See the discord documentation about how to create it and where to find it: https://discordpy.readthedocs.io/en/latest/discord.html  

Information regarding bot management and joining servers can also be found in this documentation.

## Launching

First, launch the bot in the console:
```
redbot {name}
```

Then go on discord to load the cog (the following commands must be typed in a discord server where your bot is):
```
[prefix]addpath <path_to_leaguepedia_cog>
[prefix]load leaguepedia # prefix is the prefix chosen during setup earlier
```

And you're good to go.
