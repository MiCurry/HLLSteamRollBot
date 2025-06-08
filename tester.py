import sys
import asyncio

from CRCON_Interface import CRCON_Interface
import steamrollbot


async def main():
    server = CRCON_Interface('glows east', 'https://scoreboard-us-east-1.glows.gg/')

    current_game = await server.get_current_game()

    print("Current Game: ", current_game)

    res = await server.is_game_over(current_game)

    print("Result: ", res)

    past_game = {'map_id' : 'PHL_L_1944_OffensiveUS', 'start_time_s' : 1749399768}

    res = await server.is_game_over(past_game)

    print("Result ", res)

    game = await server.get_game(past_game)

    print(game)
    
    hllgame = steamrollbot.process_game(server, game)
    print(hllgame)
    steamrollbot.was_steamroll(hllgame)

    current = await server.get_current_game_stats()
    print(current)




asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())