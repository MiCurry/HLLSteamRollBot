import traceback

from dataclasses import dataclass
import datetime

import asyncio
import discord 
from discord.ext import tasks

from HllServer import HLLServer
from HLLStatsDigester import GameState

CHANNEL_ID = 1380967531673682020

with open('.token', 'r') as file:
    token = file.read()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

#server = HLLServer('Glow\'s East', 'https://scoreboard-us-east-1.glows.gg/')
server = HLLServer('soul one', 'https://soul-one-stats.hlladmin.com/')
current_game = None


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
    if current_game.map == game.map and current_game.start_time_s == game.start_time_s:
        stats, public_info = await server.get_current_game_stats()

        if is_server_empty(public_info):
            print("The server is empty!")
            current_game.state = GameState.EMPTY
            #await channel.send(f"The server is empty!")
        elif is_server_seeding(public_info):
            print(f"The server is seeding! Number of players: {len(stats['result']['stats'])}")
            current_game.state = GameState.SEEDING
            #await channel.send(f"The server is seeding! Number of players: {len(stats['result']['stats'])}")
        else:
            await current_game.add_stat_slice(stats, public_info)
            print(f"Game is still on {current_game.map}... Time Left: {current_game.time_remaining/60} - Score: {current_game.score}")
            await channel.send(f"Game is still on {current_game.map}... Time Left: {current_game.time_remaining/60}  - Score: {current_game.score}")
            
        current_game = game
        return

    # Check if the game is actually over
    if not await server.is_game_over(current_game):
        print("Something is wrong.. game has changed but doesn't appear to be over")
        return

    game_result = await server.get_game(current_game)
    await channel.send(f"game is over on {current_game.map}!")
    print(f"Game is over on {current_game.map}!")
    print("Result:", game_result)

    current_game.process_game_result(game_result)

    if current_game.was_steamroll():
        print(f"Steam roll for current_game {current_game.map} was a steamroll! {current_game.result['steamroll_reason']} Winner: {current_game.winner} Loser: {current_game.loser}")
        await channel.send(f"Steam roll for current_game {current_game.map} was a steamroll! {current_game.result['steamroll_reason']} Winner: {current_game.winner} Loser: {current_game.loser}")
    else:
        print(f"Game on {current_game.map} was not a steamroll. Reason: {current_game.result['steamroll_raeson']} - Score: {current_game.score}")
        await channel.send(f"Game on {current_game.map} was not a steamroll. Reason: {current_game.result['steamroll_raeson']} - Score: {current_game.score}")


    current_game = None

if __name__ == "__main__":
    client.run(token)