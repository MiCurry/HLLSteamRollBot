import datetime
import sys
import asyncio
import time

import numpy as np
np.set_printoptions(precision=3, suppress=True)

from HllServer import HLLServer
from HLLStatsDigester import HllGame, HllGameStatsSlice, HllSideStats


async def main():
    server = HLLServer('glows east', 'https://scoreboard-us-east-1.glows.gg/')

    current_game = await server.get_current_game()

    res = await server.is_game_over(current_game)

    past_game = {'map_id' : 'PHL_L_1944_OffensiveUS', 'start_time_s' : 1749399768}

    res = await server.is_game_over(past_game)


    game = await server.get_game(past_game)

    hllgame = runner.process_game(server, game)
    runner.was_steamroll(hllgame)

    current, info = await server.get_current_game_stats()

    stats = process_stats(current)

    time_remaining = datetime.timedelta(seconds=info['result']['time_remaining'])

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


async def test_hllStatsDigester():
    #server = HLLServer('glows east', 'https://scoreboard-us-east-1.glows.gg/')
    server = HLLServer('soul one', 'https://soul-one-stats.hlladmin.com/')

    hllGame = HllGameStats()

    stats, public = await server.get_current_game_stats()

    hllGame.process_stats(stats, public)
    

    pass

async def test_process_games():
    server = HLLServer('glows east', 'https://scoreboard-us-central-1.glows.gg/')

    games = await server.get_history()

    for game in games:
        hllgame = HllGame()
        hllgame.process_game_result(game)
        if hllgame.was_steamroll():
            print("Was steamroll", hllgame)

async def test_stats_to_numpy():
    server = HLLServer('glows east', 'https://scoreboard-us-central-1.glows.gg/')

    current_game = await server.get_current_game()
    stats, public_info = await server.get_current_game_stats()
    current_game.add_stat_slice(stats, public_info)

    time.sleep(5)

    stats, public_info = await server.get_current_game_stats()
    current_game.add_stat_slice(stats, public_info)

    current_game.to_numpy()
    current_game.save_stat_slice('foo.csv')

    current_game.save_y('foo.csv')




asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(test_stats_to_numpy())