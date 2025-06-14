import traceback

from dataclasses import dataclass
import datetime

import asyncio
import discord 
from discord.ext import tasks

from CRCON_Interface import RCRON_TIME_STR_FORMAT, CRCON_Interface
from HLLStatsDigester import process_stats

CHANNEL_ID = 1380967531673682020

with open('.token', 'r') as file:
    token = file.read()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

server = CRCON_Interface('Glow\'s East', 'https://scoreboard-us-east-1.glows.gg/')
current_game = None

@dataclass
class HLLGame:
    id : str
    game_web_url : str
    map_name : str
    game_mode : str
    start_time : datetime.datetime
    end_time : datetime.datetime
    duration : datetime.timedelta
    axis_score :  int
    allied_score : int

def was_steamroll(game: HLLGame, threshold_minutes=30):
    if game.game_mode != 'warfare':
        return False, f"Was an Offensive game", None, None
    
    if game.duration > datetime.timedelta(minutes=threshold_minutes):
        return False, f"Was greater than {threshold_minutes} minutes", None, None

    if game.axis_score is None or game.allied_score is None:
        return False, f"Game in progress", None, None

    if game.axis_score > game.allied_score:
        winner = 'Axis'
        loser = 'Allies'
    else:
        winner = 'Allies'
        loser = 'Axis'

    return True, f"Less than {threshold_minutes} minutes", winner, loser

def process_game(server, game) -> HLLGame:
    start_time=datetime.datetime.strptime(game['start'], RCRON_TIME_STR_FORMAT)
    end_time=datetime.datetime.strptime(game['end'], RCRON_TIME_STR_FORMAT)
    duration = end_time - start_time

    if game['result'] is None:
        axis_score = None
        allied_score = None
    else:
        axis_score=int(game['result']['axis'])
        allied_score=int(game['result']['allied'])
        
    return HLLGame(
        id = game['id'],
        game_web_url = f'{server.uri}/api/games/{str(game['id'])}',
        map_name=game['map']['pretty_name'],
        game_mode=game['map']['game_mode'],
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        axis_score=axis_score,
        allied_score=allied_score
    )

@client.event
async def on_ready():
    channel = client.get_channel(CHANNEL_ID)
    await check_for_steamroll.start()
    print(f"We have logged in as {client.user}")
    await channel.send("We are running!")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello, world!')

def is_server_empty(public_info) -> bool:
    if public_info['result']['player_count'] == 0:
        return True
    
    return False

def is_server_seeding(public_info) -> bool:
    nallies = public_info['result']['player_count_by_team']['allied']
    naxies = public_info['result']['player_count_by_team']['axis']
    
    if nallies < 25 and naxies < 25:
        return True
    
    return False

import numpy as np
def process_n_print_stats(info, stats_raw):
    print("Inside process_n_print_stats")
    time_remaining = datetime.timedelta(seconds=info['result']['time_remaining'])
    stats = process_stats(stats_raw)


    print("")
    print(f"Map: {info['result']['current_map']['map']['pretty_name']}")
    print(f"Time Left: {time_remaining}")
    print("Axis - Allies")
    print(f"{info['result']['score']['axis']} - {info['result']['score']['allied']}")

    for stat_name in stats['allied'].keys():
        if (type(stats['allied'][stat_name]) == np.ndarray
            or stat_name == 'side'):
            continue 

        stat_axis = stats['axis'][stat_name]
        stat_allied = stats['allied'][stat_name]
        print(f'{stat_name}: \t {stat_axis:,.2f} - {stat_allied:,.2f}')



@tasks.loop(minutes=2)
async def check_for_steamroll():
    print("We are checking for a steamroll...")
    global server
    global current_game

    channel = client.get_channel(CHANNEL_ID)

    game = await server.get_current_game()

    if current_game == None:
        current_game = game

    # Game is not over
    if current_game['map_id'] == game['map_id'] and game['start_time_s'] == current_game['start_time_s']:
        stats, public_info = await server.get_current_game_stats()
        if is_server_empty(public_info):
            print("The server is empty!")
            #await channel.send(f"The server is empty!")
        elif is_server_seeding(public_info):
            print(f"The server is seeding! Number of players: {len(stats['result']['stats'])}")
            #await channel.send(f"The server is seeding! Number of players: {len(stats['result']['stats'])}")
        else:
            time_remaining = datetime.timedelta(seconds=public_info['result']['time_remaining'])
            score = f"Ax: {public_info['result']['score']['axis']} Al: {public_info['result']['score']['allied']}"
            print(f"Game is still on {current_game['map_id']}... Time Left: {time_remaining} - Score: {score}")
            process_n_print_stats(public_info, stats)
            await channel.send(f"Game is still on {current_game['map_id']}... Time Left: {time_remaining} - Score: {score}")
            
        current_game = game
        current_game['stats'].append(stats)
        #print(f"Current game: {current_game}")
        return

    # Check if the game is actually over
    if not await server.is_game_over(current_game):
        print("Something is wrong.. game has changed but doesn't appear to be over")
        return

    game_result = await server.get_game(current_game)
    await channel.send(f"game is over on {current_game['map_id']}!")
    print(f"Game is over on {current_game['map_id']}!")
    print("Result:", game_result)

    try:
        result = process_game(server, game_result) 
    except Exception as e:
        print(f"Error there was an exception in 'process_game'", e)
        print(traceback.format_exc())
        await channel.send("We had an exception in 'process_game'...")

    try:
        was_steamroll_result, reason, winner, loser = was_steamroll(result)
        if was_steamroll_result:
            print(f"Steam roll for game {current_game['map_id']} - {was_steamroll_result}, {reason}, Winner: {winner} Loser: {loser}")
            await channel.send(f"Game {current_game['map_id']} was a steamroll! {reason} Winner: {winner} Loser: {loser}")
        else:
            print(f"Game on {current_game['map_id']} was NOT a steam roll - {reason}")
            await channel.send(f"Game {current_game['map_id']} was NOT a steamroll! - {reason}")
    except Exception as e:
        print("There was an exception in was_streamroll..", e)
        print(traceback.format_exc())
        await channel.send("We had an exception in 'was_steamroll'...")

    current_game = None

if __name__ == "__main__":
    client.run(token)