import datetime
import sys
import asyncio

import numpy as np
np.set_printoptions(precision=3, suppress=True)

from HllServer import HLLServer
from HLLStatsDigester import HllGameStatsSlice, HllSideStats
import runner


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

    hllGame = HllGameStatsSlice()

    stats, public = await server.get_current_game_stats()

    hllGame.process_stats(stats, public)
    

    pass


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(test_hllStatsDigester())